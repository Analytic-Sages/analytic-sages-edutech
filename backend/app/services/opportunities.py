from __future__ import annotations

import logging
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from urllib.parse import urlparse
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.opportunity import (
    BountyCategory,
    CareerPath,
    EmploymentType,
    ExperienceLevel,
    HackathonEventFormat,
    LocationRegion,
    Opportunity,
    OpportunityBountyDetails,
    OpportunityCareerPath,
    OpportunityHackathonDetails,
    OpportunityPublicBadge,
    OpportunitySkill,
    OpportunitySource,
    OpportunityStatus,
    OpportunityTrustStatus,
    OpportunityType,
    Skill,
    VerificationEvent,
    VerificationEventResult,
    VerificationEventType,
    WorkplaceType,
)
from app.models.user import User
from app.schemas.opportunities import (
    AdminTaxonomy,
    BountyDetailsPublic,
    BountyDetailsWrite,
    CareerPathAdmin,
    CareerPathPublic,
    FilterOption,
    HackathonDetailsPublic,
    HackathonDetailsWrite,
    OpportunityAdmin,
    OpportunityAdminList,
    OpportunityCardPublic,
    OpportunityCreate,
    OpportunityFiltersPublic,
    OpportunityListPublic,
    OpportunityPublic,
    OpportunityUpdate,
    RiskFlagAdmin,
    SkillAdmin,
    SkillPublic,
    SourceAdmin,
    SourcePublic,
    TaxonomyOption,
)
from app.services.bounty_dates import PHASE_RANK as BOUNTY_PHASE_RANK
from app.services.bounty_dates import BountyPhase, closes_in_days
from app.services.bounty_details import refresh_derived_phase as refresh_bounty_phase
from app.services.bounty_details import upsert_bounty_details
from app.services.bounty_normalize import BountyDetailsPayload
from app.services.hackathon_dates import PHASE_RANK, HackathonPhase, registration_closes_in_days
from app.services.hackathon_details import refresh_derived_phase, upsert_hackathon_details
from app.services.hackathon_normalize import HackathonDetailsPayload
from app.services.insights import slugify
from app.services.opportunity_prose import normalize_description, normalize_optional
from app.services.opportunity_urls import validate_http_url

logger = logging.getLogger(__name__)

HTML_RE = re.compile(r"<[^>]+>")
RESERVED_SLUGS = {
    "jobs",
    "internships",
    "fellowships",
    "grants",
    "hackathons",
    "bounties",
    "research",
    "filters",
    "new",
}
TYPE_LABELS = {
    OpportunityType.JOB: "Jobs",
    OpportunityType.INTERNSHIP: "Internships",
    OpportunityType.FELLOWSHIP: "Fellowships",
    OpportunityType.HACKATHON: "Hackathons",
    OpportunityType.GRANT: "Grants",
    OpportunityType.BOUNTY: "Bounties",
    OpportunityType.CHALLENGE: "Challenges",
    OpportunityType.RESEARCH: "Research",
    OpportunityType.OTHER: "Other",
}
WORKPLACE_LABELS = {
    WorkplaceType.REMOTE: "Remote",
    WorkplaceType.HYBRID: "Hybrid",
    WorkplaceType.ONSITE: "Onsite",
}
EXPERIENCE_LABELS = {
    ExperienceLevel.INTERN: "Intern",
    ExperienceLevel.JUNIOR: "Junior",
    ExperienceLevel.MID: "Mid-level",
    ExperienceLevel.SENIOR: "Senior",
    ExperienceLevel.LEAD: "Lead",
    ExperienceLevel.NOT_SPECIFIED: "Not specified",
}
REGION_LABELS = {
    LocationRegion.GLOBAL: "Global",
    LocationRegion.AFRICA: "Africa",
    LocationRegion.NIGERIA: "Nigeria",
    LocationRegion.EUROPE: "Europe",
    LocationRegion.NORTH_AMERICA: "North America",
    LocationRegion.ASIA: "Asia",
    LocationRegion.REMOTE: "Remote",
}
CLOSING_SOON_DAYS = 14


def _enum_value(value: object) -> str:
    return value.value if hasattr(value, "value") else str(value)


class OpportunityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _utcnow(self) -> datetime:
        return datetime.now(UTC)

    def _aware(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _reject_html(self, text: str | None, field: str) -> None:
        if text and HTML_RE.search(text):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field} cannot contain HTML",
            )

    def _validate_http_url(self, url: str, field: str) -> str:
        return validate_http_url(url, field)

    def _validate_text_fields(self, payload: OpportunityCreate | OpportunityUpdate) -> None:
        mapping = {
            "title": payload.title,
            "organization_name": payload.organization_name,
            "description": payload.description,
            "requirements": payload.requirements,
            "responsibilities": payload.responsibilities,
            "benefits": payload.benefits,
            "admin_notes": getattr(payload, "admin_notes", None),
            "location": payload.location,
        }
        for field, value in mapping.items():
            if isinstance(value, str):
                self._reject_html(value, field)

    def _ensure_slug(self, title: str, slug: str | None, *, exclude_id: UUID | None = None) -> str:
        base = slug or slugify(title)[:180]
        if len(base) < 3:
            base = f"{base}-opportunity"[:180]
        if base in RESERVED_SLUGS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That slug is reserved for a public hub page",
            )
        candidate = base
        suffix = 2
        while True:
            query = select(Opportunity.id).where(Opportunity.slug == candidate)
            if exclude_id:
                query = query.where(Opportunity.id != exclude_id)
            taken = self.db.scalar(query)
            if not taken:
                return candidate
            if slug:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An opportunity with this slug already exists",
                )
            candidate = f"{base[:170]}-{suffix}"
            suffix += 1

    def _visible_now(self, now: datetime | None = None):
        current = now or self._utcnow()
        not_ended_hackathon = ~exists(
            select(OpportunityHackathonDetails.opportunity_id).where(
                OpportunityHackathonDetails.opportunity_id == Opportunity.id,
                OpportunityHackathonDetails.derived_phase == HackathonPhase.ENDED.value,
            )
        )
        not_ended_bounty = ~exists(
            select(OpportunityBountyDetails.opportunity_id).where(
                OpportunityBountyDetails.opportunity_id == Opportunity.id,
                OpportunityBountyDetails.derived_phase == BountyPhase.ENDED.value,
            )
        )
        return and_(
            Opportunity.status == OpportunityStatus.PUBLISHED,
            or_(Opportunity.deadline.is_(None), Opportunity.deadline >= current),
            not_ended_hackathon,
            not_ended_bounty,
        )

    def _detail_load(self):
        return (
            selectinload(Opportunity.career_path_links).selectinload(OpportunityCareerPath.career_path),
            selectinload(Opportunity.skill_links).selectinload(OpportunitySkill.skill),
            selectinload(Opportunity.source),
            selectinload(Opportunity.risk_flags),
            selectinload(Opportunity.hackathon_details),
            selectinload(Opportunity.bounty_details),
        )

    def _hackathon_public(self, opportunity: Opportunity) -> HackathonDetailsPublic | None:
        details = opportunity.hackathon_details
        if details is None:
            if opportunity.opportunity_type not in {
                OpportunityType.HACKATHON,
                OpportunityType.CHALLENGE,
            }:
                return None
            return None
        closes = registration_closes_in_days(
            details.registration_deadline,
            fallback_deadline=opportunity.deadline,
        )
        return HackathonDetailsPublic(
            short_description=details.short_description,
            registration_url=details.registration_url,
            website_url=details.website_url,
            registration_open_at=details.registration_open_at,
            registration_deadline=details.registration_deadline,
            start_at=details.start_at,
            end_at=details.end_at,
            submission_deadline=details.submission_deadline,
            event_format=_enum_value(details.event_format),
            prize_pool_amount=details.prize_pool_amount,
            prize_currency=details.prize_currency,
            prize_pool_raw=details.prize_pool_raw,
            team_size_min=details.team_size_min,
            team_size_max=details.team_size_max,
            tags=[str(t) for t in (details.tags or [])],
            tracks=[str(t) for t in (details.tracks or [])],
            derived_phase=details.derived_phase,
            registration_closes_in_days=closes,
        )

    def _apply_hackathon_write(
        self,
        opportunity: Opportunity,
        payload: HackathonDetailsWrite | None,
    ) -> None:
        if payload is None:
            return
        if opportunity.opportunity_type not in {
            OpportunityType.HACKATHON,
            OpportunityType.CHALLENGE,
        }:
            return
        details_payload = HackathonDetailsPayload(
            short_description=payload.short_description,
            registration_url=payload.registration_url,
            website_url=payload.website_url,
            registration_open_at=self._aware(payload.registration_open_at),
            registration_deadline=self._aware(payload.registration_deadline),
            start_at=self._aware(payload.start_at),
            end_at=self._aware(payload.end_at),
            submission_deadline=self._aware(payload.submission_deadline),
            event_format=payload.event_format,
            prize_pool_amount=payload.prize_pool_amount,
            prize_currency=payload.prize_currency,
            prize_pool_raw=payload.prize_pool_raw,
            team_size_min=payload.team_size_min,
            team_size_max=payload.team_size_max,
            team_required=payload.team_required,
            individual_allowed=payload.individual_allowed,
            tags=list(payload.tags or []),
            tracks=list(payload.tracks or []),
            technology_focus=payload.technology_focus,
            opportunity_type=opportunity.opportunity_type,
        )
        row = upsert_hackathon_details(opportunity, payload=details_payload)
        if row is not None:
            refresh_derived_phase(row)

    def _bounty_public(self, opportunity: Opportunity) -> BountyDetailsPublic | None:
        details = opportunity.bounty_details
        if details is None:
            return None
        return BountyDetailsPublic(
            short_description=details.short_description,
            listing_url=details.listing_url,
            reward_amount=details.reward_amount,
            reward_token=details.reward_token,
            reward_currency=details.reward_currency,
            reward_raw=details.reward_raw,
            category=_enum_value(details.category),
            opens_at=details.opens_at,
            deadline=details.deadline,
            winners_announced=details.winners_announced,
            skills=[str(s) for s in (details.skills or [])],
            tags=[str(t) for t in (details.tags or [])],
            chain_focus=details.chain_focus,
            derived_phase=details.derived_phase,
            closes_in_days=closes_in_days(
                details.deadline,
                fallback_deadline=opportunity.deadline,
            ),
        )

    def _apply_bounty_write(
        self,
        opportunity: Opportunity,
        payload: BountyDetailsWrite | None,
    ) -> None:
        if payload is None:
            return
        if opportunity.opportunity_type != OpportunityType.BOUNTY:
            return
        details_payload = BountyDetailsPayload(
            short_description=payload.short_description,
            listing_url=payload.listing_url,
            reward_amount=payload.reward_amount,
            reward_token=payload.reward_token,
            reward_currency=payload.reward_currency,
            reward_raw=payload.reward_raw,
            reward_min=payload.reward_min,
            reward_max=payload.reward_max,
            category=payload.category,
            opens_at=self._aware(payload.opens_at),
            deadline=self._aware(payload.deadline),
            winners_announced=payload.winners_announced,
            skills=list(payload.skills or []),
            tags=list(payload.tags or []),
            chain_focus=payload.chain_focus,
        )
        row = upsert_bounty_details(opportunity, payload=details_payload)
        if row is not None:
            refresh_bounty_phase(row)

    def _career_paths(self, opportunity: Opportunity) -> list[CareerPathPublic]:
        links = sorted(
            opportunity.career_path_links,
            key=lambda item: (not item.is_primary, -float(item.relevance_score or 0)),
        )
        rows: list[CareerPathPublic] = []
        for link in links:
            path = link.career_path
            if not path or not path.is_active:
                continue
            rows.append(
                CareerPathPublic(
                    id=path.id,
                    name=path.name,
                    slug=path.slug,
                    description=path.description,
                    is_primary=link.is_primary,
                    relevance_score=float(link.relevance_score) if link.relevance_score is not None else None,
                )
            )
        return rows

    def _skills(self, opportunity: Opportunity) -> list[SkillPublic]:
        rows: list[SkillPublic] = []
        for link in opportunity.skill_links:
            skill = link.skill
            if not skill or not skill.is_active:
                continue
            rows.append(
                SkillPublic(
                    id=skill.id,
                    name=skill.name,
                    slug=skill.slug,
                    category=skill.category,
                    importance=_enum_value(link.importance),
                )
            )
        return rows

    def _application_domain(self, url: str | None) -> str | None:
        if not url:
            return None
        host = urlparse(url).hostname
        return host.lower() if host else None

    def _is_closing_soon(self, deadline: datetime | None, now: datetime | None = None) -> bool:
        if deadline is None:
            return False
        current = now or self._utcnow()
        due = self._aware(deadline)
        if due is None or due < current:
            return False
        return due <= current + timedelta(days=CLOSING_SOON_DAYS)

    def _card(self, opportunity: Opportunity) -> OpportunityCardPublic:
        paths = self._career_paths(opportunity)
        primary = next((item for item in paths if item.is_primary), paths[0] if paths else None)
        return OpportunityCardPublic(
            id=opportunity.id,
            slug=opportunity.slug,
            title=opportunity.title,
            organization_name=opportunity.organization_name,
            opportunity_type=_enum_value(opportunity.opportunity_type),
            employment_type=_enum_value(opportunity.employment_type) if opportunity.employment_type else None,
            experience_level=_enum_value(opportunity.experience_level),
            location=opportunity.location,
            location_raw=opportunity.location_raw,
            location_scope=_enum_value(opportunity.location_scope) if opportunity.location_scope else None,
            country=opportunity.country,
            region=opportunity.region,
            workplace_type=_enum_value(opportunity.workplace_type),
            deadline=opportunity.deadline,
            published_at=opportunity.published_at,
            featured=opportunity.featured,
            closing_soon=self._is_closing_soon(opportunity.deadline),
            public_badge=_enum_value(opportunity.public_badge),
            application_domain=self._application_domain(opportunity.application_url),
            primary_career_path=primary,
            skills=self._skills(opportunity),
            source=SourcePublic(
                id=opportunity.source.id if opportunity.source else None,
                name=opportunity.source.name if opportunity.source else "Manual",
                source_type=_enum_value(opportunity.source.source_type)
                if opportunity.source
                else "manual",
            )
            if opportunity.source or opportunity.is_manual
            else None,
            hackathon=self._hackathon_public(opportunity),
            bounty=self._bounty_public(opportunity),
        )

    def _decorate_card(self, card: OpportunityCardPublic, opportunity: Opportunity, user: User | None) -> OpportunityCardPublic:
        if user is None:
            return card
        from app.services.opportunity_saves import OpportunityEngagementService, match_score

        engagement = OpportunityEngagementService(self.db)
        saves = engagement.save_map(user, [opportunity.id])
        save = saves.get(opportunity.id)
        card.saved = save is not None
        card.applied = bool(save and save.state.value == "applied")
        card.match_score = match_score(opportunity, set(engagement.interest_path_ids(user)))
        return card

    def _admin(self, opportunity: Opportunity) -> OpportunityAdmin:
        source = opportunity.source
        paths: list[CareerPathAdmin] = []
        for link in opportunity.career_path_links:
            path = link.career_path
            if not path:
                continue
            paths.append(
                CareerPathAdmin(
                    id=path.id,
                    name=path.name,
                    slug=path.slug,
                    description=path.description,
                    is_active=path.is_active,
                    is_primary=link.is_primary,
                    relevance_score=float(link.relevance_score) if link.relevance_score is not None else None,
                )
            )
        skills: list[SkillAdmin] = []
        for link in opportunity.skill_links:
            skill = link.skill
            if not skill:
                continue
            skills.append(
                SkillAdmin(
                    id=skill.id,
                    name=skill.name,
                    slug=skill.slug,
                    category=skill.category,
                    is_active=skill.is_active,
                    importance=_enum_value(link.importance),
                )
            )
        return OpportunityAdmin(
            id=opportunity.id,
            slug=opportunity.slug,
            title=opportunity.title,
            organization_name=opportunity.organization_name,
            description=normalize_description(opportunity.description),
            requirements=normalize_description(opportunity.requirements or ""),
            responsibilities=normalize_optional(opportunity.responsibilities),
            benefits=normalize_optional(opportunity.benefits),
            opportunity_type=_enum_value(opportunity.opportunity_type),
            employment_type=_enum_value(opportunity.employment_type) if opportunity.employment_type else None,
            experience_level=_enum_value(opportunity.experience_level),
            location=opportunity.location,
            location_raw=opportunity.location_raw,
            location_scope=_enum_value(opportunity.location_scope) if opportunity.location_scope else None,
            country=opportunity.country,
            region=opportunity.region,
            workplace_type=_enum_value(opportunity.workplace_type),
            application_url=opportunity.application_url,
            source_url=opportunity.source_url,
            deadline=opportunity.deadline,
            published_at=opportunity.published_at,
            expires_at=opportunity.expires_at,
            status=opportunity.status,
            source_id=opportunity.source_id,
            source=self._source_admin(source) if source else None,
            trust_score=opportunity.trust_score,
            trust_status=opportunity.trust_status,
            public_badge=opportunity.public_badge,
            featured=opportunity.featured,
            admin_notes=opportunity.admin_notes,
            is_manual=opportunity.is_manual,
            external_id=opportunity.external_id,
            relevance_score=opportunity.relevance_score,
            match_reasons=list(opportunity.match_reasons or []),
            matched_career_tracks=list(opportunity.matched_career_tracks or []),
            duplicate_of_id=opportunity.duplicate_of_id,
            duplicate_confidence=opportunity.duplicate_confidence,
            created_by=opportunity.created_by,
            approved_by=opportunity.approved_by,
            career_paths=paths,
            skills=skills,
            risk_flags=[
                RiskFlagAdmin(
                    flag_type=flag.flag_type,
                    severity=_enum_value(flag.severity),
                    description=flag.description,
                    is_resolved=flag.is_resolved,
                )
                for flag in list(getattr(opportunity, "risk_flags", []) or [])
                if not flag.is_resolved
            ],
            telegram_announced_at=opportunity.telegram_announced_at,
            review_assist=opportunity.review_assist or {},
            hackathon=self._hackathon_public(opportunity),
            bounty=self._bounty_public(opportunity),
            created_at=opportunity.created_at,
            updated_at=opportunity.updated_at,
        )

    def _similar(self, opportunity: Opportunity, limit: int = 3) -> list[OpportunityCardPublic]:
        now = self._utcnow()
        path_ids = [link.career_path_id for link in opportunity.career_path_links]
        query = (
            select(Opportunity)
            .options(*self._detail_load())
            .where(self._visible_now(now), Opportunity.id != opportunity.id)
        )
        if path_ids:
            matching_ids = select(OpportunityCareerPath.opportunity_id).where(
                OpportunityCareerPath.career_path_id.in_(path_ids)
            )
            query = query.where(
                or_(
                    Opportunity.opportunity_type == opportunity.opportunity_type,
                    Opportunity.id.in_(matching_ids),
                )
            )
        else:
            query = query.where(Opportunity.opportunity_type == opportunity.opportunity_type)
        query = query.order_by(
            Opportunity.featured.desc(),
            Opportunity.published_at.desc().nullslast(),
        ).limit(limit)
        return [self._card(row) for row in self.db.scalars(query).all()]

    def _log(
        self,
        opportunity: Opportunity,
        event_type: VerificationEventType,
        result: VerificationEventResult,
        actor: User | None,
        notes: str | None = None,
        evidence: dict | None = None,
    ) -> None:
        self.db.add(
            VerificationEvent(
                opportunity_id=opportunity.id,
                event_type=event_type,
                result=result,
                performed_by=actor.id if actor else None,
                notes=notes,
                evidence=evidence or {},
            )
        )

    def _replace_taxonomy(
        self,
        opportunity: Opportunity,
        career_path_ids: list[UUID] | None,
        skill_ids: list[UUID] | None,
    ) -> None:
        if career_path_ids is not None:
            unique_ids = list(dict.fromkeys(career_path_ids))
            if unique_ids:
                found = {
                    row.id: row
                    for row in self.db.scalars(
                        select(CareerPath).where(CareerPath.id.in_(unique_ids), CareerPath.is_active.is_(True))
                    ).all()
                }
                missing = [str(item) for item in unique_ids if item not in found]
                if missing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="One or more career paths are invalid",
                    )
            opportunity.career_path_links.clear()
            self.db.flush()
            for index, path_id in enumerate(unique_ids):
                opportunity.career_path_links.append(
                    OpportunityCareerPath(
                        career_path_id=path_id,
                        is_primary=index == 0,
                        relevance_score=Decimal("1.000"),
                    )
                )
        if skill_ids is not None:
            unique_ids = list(dict.fromkeys(skill_ids))
            if unique_ids:
                found = {
                    row.id: row
                    for row in self.db.scalars(
                        select(Skill).where(Skill.id.in_(unique_ids), Skill.is_active.is_(True))
                    ).all()
                }
                missing = [str(item) for item in unique_ids if item not in found]
                if missing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="One or more skills are invalid",
                    )
            opportunity.skill_links.clear()
            self.db.flush()
            for skill_id in unique_ids:
                opportunity.skill_links.append(OpportunitySkill(skill_id=skill_id))

    def _apply_urls(self, opportunity: Opportunity, application_url: str | None, source_url: str | None) -> None:
        if application_url is not None:
            opportunity.application_url = self._validate_http_url(application_url, "application_url")
        if source_url is not None:
            opportunity.source_url = self._validate_http_url(source_url, "source_url") if source_url else None

    def _source_admin(self, source: OpportunitySource) -> SourceAdmin:
        return SourceAdmin(
            id=source.id,
            name=source.name,
            website_url=source.website_url,
            source_type=_enum_value(source.source_type),
            trust_level=_enum_value(source.trust_level),
            automation_enabled=source.automation_enabled,
            auto_publish_allowed=source.auto_publish_allowed,
            is_active=source.is_active,
        )

    def _get(self, opportunity_id: UUID) -> Opportunity:
        opportunity = self.db.scalar(
            select(Opportunity).options(*self._detail_load()).where(Opportunity.id == opportunity_id)
        )
        if not opportunity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
        return opportunity

    def list_public(
        self,
        *,
        q: str | None = None,
        opportunity_type: OpportunityType | None = None,
        career_path: str | None = None,
        skill: str | None = None,
        workplace_type: WorkplaceType | None = None,
        experience_level: ExperienceLevel | None = None,
        employment_type: EmploymentType | None = None,
        region: LocationRegion | None = None,
        event_format: HackathonEventFormat | None = None,
        hackathon_phase: str | None = None,
        bounty_category: BountyCategory | None = None,
        bounty_phase: str | None = None,
        sort: str = "newest",
        limit: int = 20,
        offset: int = 0,
        user: User | None = None,
    ) -> OpportunityListPublic:
        now = self._utcnow()
        filters = [self._visible_now(now)]
        query = select(Opportunity).options(*self._detail_load())
        count_query = select(func.count()).select_from(Opportunity)

        if q:
            term = f"%{q.strip()}%"
            search = or_(
                Opportunity.title.ilike(term),
                Opportunity.organization_name.ilike(term),
                Opportunity.location.ilike(term),
                Opportunity.description.ilike(term),
                Opportunity.requirements.ilike(term),
                exists(
                    select(OpportunitySkill.id)
                    .join(Skill)
                    .where(
                        OpportunitySkill.opportunity_id == Opportunity.id,
                        or_(Skill.name.ilike(term), Skill.slug.ilike(term)),
                    )
                ),
                exists(
                    select(OpportunityCareerPath.id)
                    .join(CareerPath)
                    .where(
                        OpportunityCareerPath.opportunity_id == Opportunity.id,
                        or_(CareerPath.name.ilike(term), CareerPath.slug.ilike(term)),
                    )
                ),
            )
            filters.append(search)
        if opportunity_type:
            filters.append(Opportunity.opportunity_type == opportunity_type)
        if workplace_type:
            filters.append(Opportunity.workplace_type == workplace_type)
        if experience_level:
            filters.append(Opportunity.experience_level == experience_level)
        if employment_type:
            filters.append(Opportunity.employment_type == employment_type)
        if region:
            filters.append(Opportunity.region == region.value)
        if event_format is not None:
            filters.append(
                exists(
                    select(OpportunityHackathonDetails.opportunity_id).where(
                        OpportunityHackathonDetails.opportunity_id == Opportunity.id,
                        OpportunityHackathonDetails.event_format == event_format,
                    )
                )
            )
        if hackathon_phase:
            filters.append(
                exists(
                    select(OpportunityHackathonDetails.opportunity_id).where(
                        OpportunityHackathonDetails.opportunity_id == Opportunity.id,
                        OpportunityHackathonDetails.derived_phase == hackathon_phase,
                    )
                )
            )
        if bounty_category is not None:
            filters.append(
                exists(
                    select(OpportunityBountyDetails.opportunity_id).where(
                        OpportunityBountyDetails.opportunity_id == Opportunity.id,
                        OpportunityBountyDetails.category == bounty_category,
                    )
                )
            )
        if bounty_phase:
            filters.append(
                exists(
                    select(OpportunityBountyDetails.opportunity_id).where(
                        OpportunityBountyDetails.opportunity_id == Opportunity.id,
                        OpportunityBountyDetails.derived_phase == bounty_phase,
                    )
                )
            )
        if career_path:
            try:
                path_uuid = UUID(career_path)
                path_match = CareerPath.id == path_uuid
            except ValueError:
                path_match = CareerPath.slug == career_path
            filters.append(
                Opportunity.id.in_(
                    select(OpportunityCareerPath.opportunity_id).join(CareerPath).where(path_match)
                )
            )
        if skill:
            try:
                skill_uuid = UUID(skill)
                skill_match = Skill.id == skill_uuid
            except ValueError:
                skill_match = Skill.slug == skill
            filters.append(
                Opportunity.id.in_(
                    select(OpportunitySkill.opportunity_id).join(Skill).where(skill_match)
                )
            )

        query = query.where(*filters)
        count_query = count_query.where(*filters)
        interest_ids: set[UUID] = set()
        if user is not None and sort == "matched":
            from app.services.opportunity_saves import OpportunityEngagementService, match_score

            engagement = OpportunityEngagementService(self.db)
            interest_ids = set(engagement.interest_path_ids(user))
            if interest_ids:
                filters.append(
                    Opportunity.id.in_(
                        select(OpportunityCareerPath.opportunity_id).where(
                            OpportunityCareerPath.career_path_id.in_(interest_ids)
                        )
                    )
                )
                query = select(Opportunity).options(*self._detail_load()).where(*filters)
                count_query = select(func.count()).select_from(Opportunity).where(*filters)
                rows = list(self.db.scalars(query).all())
                rows.sort(key=lambda row: match_score(row, interest_ids) or 0, reverse=True)
                total = len(rows)
                page = rows[offset : offset + limit]
                return OpportunityListPublic(
                    items=[self._decorate_card(self._card(row), row, user) for row in page],
                    total=total,
                    limit=limit,
                    offset=offset,
                )

        is_hackathon_feed = opportunity_type in {
            OpportunityType.HACKATHON,
            OpportunityType.CHALLENGE,
        } or sort == "hackathon"
        if is_hackathon_feed and sort in {"newest", "hackathon", "deadline"}:
            rows = list(self.db.scalars(query).all())

            def _hackathon_sort_key(row: Opportunity):
                details = row.hackathon_details
                phase = HackathonPhase.UNKNOWN
                if details and details.derived_phase:
                    try:
                        phase = HackathonPhase(details.derived_phase)
                    except ValueError:
                        phase = HackathonPhase.UNKNOWN
                reg = None
                if details and details.registration_deadline:
                    reg = self._aware(details.registration_deadline)
                elif row.deadline:
                    reg = self._aware(row.deadline)
                return (
                    PHASE_RANK.get(phase, 99),
                    reg or datetime.max.replace(tzinfo=UTC),
                    -(row.published_at.timestamp() if row.published_at else 0),
                )

            rows.sort(key=_hackathon_sort_key)
            total = len(rows)
            page = rows[offset : offset + limit]
            return OpportunityListPublic(
                items=[self._decorate_card(self._card(row), row, user) for row in page],
                total=total,
                limit=limit,
                offset=offset,
            )

        is_bounty_feed = opportunity_type == OpportunityType.BOUNTY or sort == "bounty"
        if is_bounty_feed and sort in {"newest", "bounty", "deadline"}:
            rows = list(self.db.scalars(query).all())

            def _bounty_sort_key(row: Opportunity):
                details = row.bounty_details
                phase = BountyPhase.UNKNOWN
                if details and details.derived_phase:
                    try:
                        phase = BountyPhase(details.derived_phase)
                    except ValueError:
                        phase = BountyPhase.UNKNOWN
                due = None
                if details and details.deadline:
                    due = self._aware(details.deadline)
                elif row.deadline:
                    due = self._aware(row.deadline)
                reward = float(details.reward_amount) if details and details.reward_amount is not None else 0.0
                return (
                    BOUNTY_PHASE_RANK.get(phase, 99),
                    due or datetime.max.replace(tzinfo=UTC),
                    -reward,
                )

            rows.sort(key=_bounty_sort_key)
            total = len(rows)
            page = rows[offset : offset + limit]
            return OpportunityListPublic(
                items=[self._decorate_card(self._card(row), row, user) for row in page],
                total=total,
                limit=limit,
                offset=offset,
            )

        if sort == "deadline":
            query = query.order_by(
                Opportunity.deadline.asc().nullslast(),
                Opportunity.published_at.desc().nullslast(),
            )
        elif sort == "closing_soon":
            soon = now + timedelta(days=CLOSING_SOON_DAYS)
            query = query.where(Opportunity.deadline.is_not(None), Opportunity.deadline <= soon)
            count_query = count_query.where(Opportunity.deadline.is_not(None), Opportunity.deadline <= soon)
            query = query.order_by(Opportunity.deadline.asc())
        elif sort == "featured":
            query = query.order_by(
                Opportunity.featured.desc(),
                Opportunity.published_at.desc().nullslast(),
            )
        else:
            query = query.order_by(
                Opportunity.featured.desc(),
                Opportunity.published_at.desc().nullslast(),
                Opportunity.created_at.desc(),
            )

        total = int(self.db.scalar(count_query) or 0)
        rows = self.db.scalars(query.offset(offset).limit(limit)).all()
        return OpportunityListPublic(
            items=[self._decorate_card(self._card(row), row, user) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get_public(self, slug: str, user: User | None = None) -> OpportunityPublic:
        now = self._utcnow()
        opportunity = self.db.scalar(
            select(Opportunity)
            .options(*self._detail_load())
            .where(Opportunity.slug == slug, self._visible_now(now))
        )
        if not opportunity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
        card = self._decorate_card(self._card(opportunity), opportunity, user)
        source = opportunity.source
        return OpportunityPublic(
            **card.model_dump(),
            description=normalize_description(opportunity.description),
            requirements=normalize_description(opportunity.requirements or ""),
            responsibilities=normalize_optional(opportunity.responsibilities),
            benefits=normalize_optional(opportunity.benefits),
            application_url=opportunity.application_url,
            source_url=opportunity.source_url,
            career_paths=self._career_paths(opportunity),
            source=SourcePublic(
                id=source.id,
                name=source.name,
                source_type=_enum_value(source.source_type),
            )
            if source
            else None,
            updated_at=opportunity.updated_at,
            similar=self._similar(opportunity),
        )

    def list_filters(self) -> OpportunityFiltersPublic:
        now = self._utcnow()
        visible = self._visible_now(now)

        def _counts(column) -> dict[str, int]:
            rows = self.db.execute(
                select(column, func.count()).where(visible).group_by(column)
            ).all()
            return {_enum_value(value): int(count) for value, count in rows if value is not None}

        type_counts = _counts(Opportunity.opportunity_type)
        workplace_counts = _counts(Opportunity.workplace_type)
        experience_counts = _counts(Opportunity.experience_level)
        region_counts = _counts(Opportunity.region)

        path_rows = self.db.execute(
            select(CareerPath.id, CareerPath.slug, CareerPath.name, func.count(Opportunity.id))
            .outerjoin(OpportunityCareerPath, OpportunityCareerPath.career_path_id == CareerPath.id)
            .outerjoin(Opportunity, and_(Opportunity.id == OpportunityCareerPath.opportunity_id, visible))
            .where(CareerPath.is_active.is_(True))
            .group_by(CareerPath.id)
            .order_by(CareerPath.sort_order, CareerPath.name)
        ).all()
        skill_rows = self.db.execute(
            select(Skill.id, Skill.slug, Skill.name, func.count(Opportunity.id))
            .outerjoin(OpportunitySkill, OpportunitySkill.skill_id == Skill.id)
            .outerjoin(Opportunity, and_(Opportunity.id == OpportunitySkill.opportunity_id, visible))
            .where(Skill.is_active.is_(True))
            .group_by(Skill.id)
            .order_by(Skill.name)
        ).all()

        return OpportunityFiltersPublic(
            types=[
                FilterOption(value=item.value, label=TYPE_LABELS[item], count=type_counts.get(item.value, 0))
                for item in OpportunityType
                if item != OpportunityType.OTHER or type_counts.get(item.value, 0)
            ],
            career_paths=[
                TaxonomyOption(id=row[0], slug=row[1], name=row[2], count=int(row[3] or 0))
                for row in path_rows
            ],
            skills=[
                TaxonomyOption(id=row[0], slug=row[1], name=row[2], count=int(row[3] or 0))
                for row in skill_rows
            ],
            workplace_types=[
                FilterOption(value=item.value, label=WORKPLACE_LABELS[item], count=workplace_counts.get(item.value, 0))
                for item in WorkplaceType
            ],
            experience_levels=[
                FilterOption(
                    value=item.value,
                    label=EXPERIENCE_LABELS[item],
                    count=experience_counts.get(item.value, 0),
                )
                for item in ExperienceLevel
            ],
            regions=[
                FilterOption(value=item.value, label=REGION_LABELS[item], count=region_counts.get(item.value, 0))
                for item in LocationRegion
            ],
        )

    def list_admin(
        self,
        *,
        q: str | None = None,
        status_filter: OpportunityStatus | None = None,
        review_queue: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> OpportunityAdminList:
        filters = []
        if q:
            term = f"%{q.strip()}%"
            filters.append(
                or_(
                    Opportunity.title.ilike(term),
                    Opportunity.organization_name.ilike(term),
                    Opportunity.slug.ilike(term),
                )
            )
        if review_queue:
            filters.append(Opportunity.status == OpportunityStatus.DRAFT)
            filters.append(
                Opportunity.trust_status.in_(
                    (OpportunityTrustStatus.REVIEW_REQUIRED, OpportunityTrustStatus.HIGH_RISK)
                )
            )
        elif status_filter:
            filters.append(Opportunity.status == status_filter)
        query = select(Opportunity).options(*self._detail_load())
        count_query = select(func.count()).select_from(Opportunity)
        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)
        total = int(self.db.scalar(count_query) or 0)
        rows = self.db.scalars(
            query.order_by(Opportunity.updated_at.desc()).offset(offset).limit(limit)
        ).all()
        return OpportunityAdminList(
            items=[self._admin(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get_admin(self, opportunity_id: UUID) -> OpportunityAdmin:
        return self._admin(self._get(opportunity_id))

    def admin_taxonomy(self) -> AdminTaxonomy:
        paths = self.db.scalars(
            select(CareerPath).where(CareerPath.is_active.is_(True)).order_by(CareerPath.sort_order, CareerPath.name)
        ).all()
        skills = self.db.scalars(
            select(Skill).where(Skill.is_active.is_(True)).order_by(Skill.name)
        ).all()
        sources = self.db.scalars(
            select(OpportunitySource).where(OpportunitySource.is_active.is_(True)).order_by(OpportunitySource.name)
        ).all()
        return AdminTaxonomy(
            career_paths=[
                CareerPathAdmin(
                    id=row.id,
                    name=row.name,
                    slug=row.slug,
                    description=row.description,
                    is_active=row.is_active,
                )
                for row in paths
            ],
            skills=[
                SkillAdmin(
                    id=row.id,
                    name=row.name,
                    slug=row.slug,
                    category=row.category,
                    is_active=row.is_active,
                )
                for row in skills
            ],
            sources=[self._source_admin(row) for row in sources],
        )

    def create(self, payload: OpportunityCreate, actor: User) -> OpportunityAdmin:
        self._validate_text_fields(payload)
        slug = self._ensure_slug(payload.title, payload.slug)
        source_id = payload.source_id
        if source_id is None:
            manual = self.db.scalar(select(OpportunitySource).where(OpportunitySource.name == "Manual"))
            source_id = manual.id if manual else None
        elif not self.db.get(OpportunitySource, source_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source not found")

        opportunity = Opportunity(
            slug=slug,
            title=payload.title,
            organization_name=payload.organization_name,
            description=normalize_description(payload.description),
            requirements=normalize_description(payload.requirements),
            responsibilities=normalize_optional(payload.responsibilities),
            benefits=normalize_optional(payload.benefits),
            opportunity_type=payload.opportunity_type,
            employment_type=payload.employment_type,
            experience_level=payload.experience_level,
            location=payload.location,
            country=payload.country,
            region=_enum_value(payload.region) if payload.region else None,
            workplace_type=payload.workplace_type,
            deadline=self._aware(payload.deadline),
            source_id=source_id,
            public_badge=payload.public_badge,
            featured=payload.featured,
            admin_notes=payload.admin_notes,
            created_by=actor.id,
            status=OpportunityStatus.DRAFT,
            trust_status=OpportunityTrustStatus.UNVERIFIED,
        )
        self._apply_urls(opportunity, payload.application_url, payload.source_url)
        self.db.add(opportunity)
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An opportunity with this slug already exists",
            ) from exc
        self._replace_taxonomy(opportunity, payload.career_path_ids, payload.skill_ids)
        self._apply_hackathon_write(opportunity, payload.hackathon)
        self._apply_bounty_write(opportunity, payload.bounty)
        self._log(opportunity, VerificationEventType.CREATED, VerificationEventResult.RECORDED, actor)
        self.db.commit()
        return self.get_admin(opportunity.id)

    def update(self, opportunity_id: UUID, payload: OpportunityUpdate, actor: User) -> OpportunityAdmin:
        opportunity = self._get(opportunity_id)
        self._validate_text_fields(payload)
        data = payload.model_dump(exclude_unset=True)
        career_path_ids = data.pop("career_path_ids", None)
        skill_ids = data.pop("skill_ids", None)
        hackathon_data = data.pop("hackathon", None)
        bounty_data = data.pop("bounty", None)
        application_url = data.pop("application_url", None)
        source_url = data.pop("source_url", None)
        if "slug" in data:
            opportunity.slug = self._ensure_slug(
                data.get("title") or opportunity.title,
                data.pop("slug"),
                exclude_id=opportunity.id,
            )
        if "deadline" in data:
            opportunity.deadline = self._aware(data.pop("deadline"))
        if "source_id" in data:
            source_id = data.pop("source_id")
            if source_id and not self.db.get(OpportunitySource, source_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source not found")
            opportunity.source_id = source_id
        for key, value in data.items():
            setattr(opportunity, key, value)
        if "description" in data:
            opportunity.description = normalize_description(opportunity.description)
        if "requirements" in data:
            opportunity.requirements = normalize_description(opportunity.requirements or "")
        if "responsibilities" in data:
            opportunity.responsibilities = normalize_optional(opportunity.responsibilities)
        if "benefits" in data:
            opportunity.benefits = normalize_optional(opportunity.benefits)
        self._apply_urls(opportunity, application_url, source_url)
        if career_path_ids is not None or skill_ids is not None:
            self._replace_taxonomy(opportunity, career_path_ids, skill_ids)
        if "hackathon" in payload.model_fields_set:
            self._apply_hackathon_write(
                opportunity,
                HackathonDetailsWrite.model_validate(hackathon_data) if hackathon_data else None,
            )
        if "bounty" in payload.model_fields_set:
            self._apply_bounty_write(
                opportunity,
                BountyDetailsWrite.model_validate(bounty_data) if bounty_data else None,
            )
        self._log(opportunity, VerificationEventType.UPDATED, VerificationEventResult.RECORDED, actor)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An opportunity with this slug already exists",
            ) from exc
        return self.get_admin(opportunity.id)

    def _publish_block_reason(
        self,
        opportunity: Opportunity,
        *,
        skip_high_risk: bool = False,
    ) -> str | None:
        if opportunity.status == OpportunityStatus.ARCHIVED:
            return "Archived"
        if opportunity.status == OpportunityStatus.PUBLISHED:
            return "Already published"
        if opportunity.status == OpportunityStatus.REJECTED:
            return "Rejected"
        if skip_high_risk and opportunity.trust_status == OpportunityTrustStatus.HIGH_RISK:
            return "High risk — review individually"
        if not opportunity.title.strip() or not opportunity.organization_name.strip():
            return "Missing title or organization"
        if not (opportunity.description or "").strip():
            return "Missing description"
        if not opportunity.application_url:
            return "Missing application URL"
        deadline = self._aware(opportunity.deadline)
        if deadline is not None and deadline < self._utcnow():
            return "Deadline already passed"
        return None

    def _assert_can_publish(self, opportunity: Opportunity) -> None:
        reason = self._publish_block_reason(opportunity, skip_high_risk=False)
        if reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

    def publish(self, opportunity_id: UUID, actor: User, notes: str | None = None) -> OpportunityAdmin:
        opportunity = self._get(opportunity_id)
        self._assert_can_publish(opportunity)
        self._apply_publish(opportunity, actor, notes=notes)
        self.db.commit()
        from app.services.opportunity_publish import emit_opportunity_published

        emit_opportunity_published(opportunity)
        logger.info("opportunity_published id=%s slug=%s actor=%s", opportunity.id, opportunity.slug, actor.id)
        return self.get_admin(opportunity.id)

    def _apply_publish(self, opportunity: Opportunity, actor: User, notes: str | None = None) -> None:
        opportunity.status = OpportunityStatus.PUBLISHED
        if opportunity.published_at is None:
            opportunity.published_at = self._utcnow()
        opportunity.approved_by = actor.id
        if opportunity.trust_status in {
            OpportunityTrustStatus.REVIEW_REQUIRED,
            OpportunityTrustStatus.HIGH_RISK,
            OpportunityTrustStatus.UNVERIFIED,
        }:
            opportunity.trust_status = OpportunityTrustStatus.SOURCE_CHECKED
        if (
            not opportunity.is_manual
            and opportunity.public_badge == OpportunityPublicBadge.NONE
        ):
            opportunity.public_badge = OpportunityPublicBadge.SOURCE_CHECKED
        self._log(
            opportunity,
            VerificationEventType.ADMIN_APPROVAL,
            VerificationEventResult.APPROVED,
            actor,
            notes=notes,
        )

    def publish_bulk(
        self,
        actor: User,
        opportunity_ids: list[UUID],
        *,
        notes: str | None = None,
        include_high_risk: bool = False,
    ):
        from app.schemas.opportunities import (
            OpportunityBulkPublishResult,
            OpportunityBulkPublishSkipped,
        )
        from app.services.opportunity_publish import emit_opportunity_published

        if not opportunity_ids:
            return OpportunityBulkPublishResult()
        # Preserve order, drop duplicates
        seen: set[UUID] = set()
        ordered: list[UUID] = []
        for oid in opportunity_ids[:50]:
            if oid in seen:
                continue
            seen.add(oid)
            ordered.append(oid)

        published_ids: list[UUID] = []
        skipped_items: list[OpportunityBulkPublishSkipped] = []
        published_rows: list[Opportunity] = []

        for oid in ordered:
            opportunity = self.db.scalar(
                select(Opportunity).options(*self._detail_load()).where(Opportunity.id == oid)
            )
            if opportunity is None:
                skipped_items.append(
                    OpportunityBulkPublishSkipped(id=oid, title="(missing)", reason="Not found")
                )
                continue
            reason = self._publish_block_reason(
                opportunity,
                skip_high_risk=not include_high_risk,
            )
            if reason:
                skipped_items.append(
                    OpportunityBulkPublishSkipped(
                        id=opportunity.id,
                        title=opportunity.title,
                        reason=reason,
                    )
                )
                continue
            self._apply_publish(opportunity, actor, notes=notes)
            published_ids.append(opportunity.id)
            published_rows.append(opportunity)

        self.db.commit()
        for row in published_rows:
            emit_opportunity_published(row)
            logger.info("opportunity_published_bulk id=%s slug=%s actor=%s", row.id, row.slug, actor.id)

        return OpportunityBulkPublishResult(
            published=len(published_ids),
            skipped=len(skipped_items),
            published_ids=published_ids,
            skipped_items=skipped_items,
        )

    def unpublish(self, opportunity_id: UUID, actor: User, notes: str | None = None) -> OpportunityAdmin:
        opportunity = self._get(opportunity_id)
        opportunity.status = OpportunityStatus.DRAFT
        self._log(
            opportunity,
            VerificationEventType.ADMIN_UNPUBLISH,
            VerificationEventResult.UNPUBLISHED,
            actor,
            notes=notes,
        )
        self.db.commit()
        return self.get_admin(opportunity.id)

    def reject(self, opportunity_id: UUID, actor: User, notes: str | None = None) -> OpportunityAdmin:
        opportunity = self._get(opportunity_id)
        opportunity.status = OpportunityStatus.REJECTED
        self._log(
            opportunity,
            VerificationEventType.ADMIN_REJECT,
            VerificationEventResult.REJECTED,
            actor,
            notes=notes,
        )
        self.db.commit()
        return self.get_admin(opportunity.id)

    def archive(self, opportunity_id: UUID, actor: User, notes: str | None = None) -> OpportunityAdmin:
        opportunity = self._get(opportunity_id)
        opportunity.status = OpportunityStatus.ARCHIVED
        self._log(
            opportunity,
            VerificationEventType.ADMIN_ARCHIVE,
            VerificationEventResult.ARCHIVED,
            actor,
            notes=notes,
        )
        self.db.commit()
        return self.get_admin(opportunity.id)
