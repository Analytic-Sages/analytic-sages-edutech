from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.opportunity import (
    CareerPath,
    EmploymentType,
    ExperienceLevel,
    Opportunity,
    OpportunityStatus,
    OpportunityTrustStatus,
    OpportunityType,
    Skill,
)
from app.models.user import User
from app.schemas.opportunities import (
    OpportunityCreate,
    OpportunityDiscoverCandidate,
    OpportunityDiscoverImportResult,
    OpportunityDiscoverResponse,
)
from app.services.llm_complete import complete_json, llm_configured
from app.services.opportunity_extract import (
    extract_from_page_text,
    extraction_enabled,
    merge_raw_with_extraction,
)
from app.services.opportunity_mission import is_off_mission_title
from app.services.opportunity_page_fetch import fetch_public_page
from app.services.opportunity_relevance import infer_opportunity_type, score_relevance
from app.services.opportunity_sources.base import RawOpportunity
from app.services.opportunity_urls import (
    hostname_of,
    is_aggregator_url,
    is_shortened_url,
    validate_http_url,
)
from app.services.opportunities import OpportunityService

logger = logging.getLogger(__name__)

MAX_CANDIDATES = 18
DISCOVERY_TYPES = (
    OpportunityType.JOB,
    OpportunityType.INTERNSHIP,
    OpportunityType.FELLOWSHIP,
    OpportunityType.HACKATHON,
    OpportunityType.CHALLENGE,
    OpportunityType.GRANT,
    OpportunityType.BOUNTY,
    OpportunityType.RESEARCH,
)
PREFERRED_HOSTS = (
    "ethglobal.com",
    "colosseum.com",
    "devpost.com",
    "devfolio.co",
    "dorahacks.io",
    "encodeclub.com",
    "encode.club",
    "superteam.fun",
    "ethereum.foundation",
    "esp.ethereum.foundation",
    "ethereum.org",
    "gitcoin.co",
    "immunefi.com",
    "flashbots.net",
    "protocol.ai",
    "filecoin.io",
    "uniswap.org",
    "a16zcrypto.com",
    "openai.com",
    "anthropic.com",
    "deepmind.google",
)
ALLOWED_TYPES = {item.value for item in DISCOVERY_TYPES}


class OpportunityDiscoveryService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.opportunities = OpportunityService(db)

    @property
    def configured(self) -> bool:
        return llm_configured(self.settings)

    def reclassify_drafts(self) -> int:
        drafts = list(
            self.db.scalars(
                select(Opportunity).where(Opportunity.status == OpportunityStatus.DRAFT)
            ).all()
        )
        updated = 0
        for opportunity in drafts:
            inferred = infer_opportunity_type(
                RawOpportunity(
                    external_id=str(opportunity.id),
                    title=opportunity.title,
                    organization_name=opportunity.organization_name,
                    description=opportunity.description,
                    requirements=opportunity.requirements,
                    location=opportunity.location,
                    application_url=opportunity.application_url,
                )
            )
            if inferred != opportunity.opportunity_type:
                opportunity.opportunity_type = inferred
                updated += 1
        if updated:
            self.db.commit()
        return updated

    def discover(
        self,
        *,
        types: list[OpportunityType] | None = None,
        query: str | None = None,
    ) -> OpportunityDiscoverResponse:
        if not self.configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Discovery is not configured. Set OPENAI_API_KEY or GEMINI_API_KEY.",
            )
        selected = [item for item in (types or list(DISCOVERY_TYPES)) if item in DISCOVERY_TYPES]
        if not selected:
            selected = list(DISCOVERY_TYPES)
        types_updated = self.reclassify_drafts()
        paths = list(
            self.db.scalars(select(CareerPath).where(CareerPath.is_active.is_(True)).order_by(CareerPath.sort_order)).all()
        )
        raw_rows, grounded, provider = self._complete(selected, (query or "").strip(), [path.slug for path in paths])
        candidates: list[OpportunityDiscoverCandidate] = []
        dropped = 0
        seen: set[str] = set()
        for row in raw_rows:
            candidate, reason = self._sanitize(row, selected, seen)
            if reason or candidate is None:
                dropped += 1
                continue
            seen.add(_normalize_url(candidate.application_url))
            candidates.append(candidate)
            if len(candidates) >= MAX_CANDIDATES:
                break
        notes = None
        if not grounded:
            notes = "Web search was unavailable. Verify every official URL before importing."
        if provider == "gemini":
            extra = "Used Gemini after OpenAI was unavailable." if (self.settings.openai_api_key or "").strip() else "Used Gemini."
            notes = f"{notes} {extra}".strip() if notes else extra
        return OpportunityDiscoverResponse(
            configured=True,
            grounded=grounded,
            never_publishes=True,
            types_updated=types_updated,
            dropped=dropped,
            candidates=candidates,
            provider=provider,
            notes=notes,
        )

    def import_candidates(
        self,
        candidates: list[OpportunityDiscoverCandidate],
        actor: User,
    ) -> OpportunityDiscoverImportResult:
        imported: list[UUID] = []
        skipped = 0
        page_verified = 0
        extraction_failed = 0
        for candidate in candidates[:MAX_CANDIDATES]:
            cleaned, reason = self._sanitize(candidate.model_dump(), list(DISCOVERY_TYPES), set())
            if reason or cleaned is None:
                skipped += 1
                continue
            if self._find_by_url(cleaned.application_url):
                skipped += 1
                continue
            grounded_candidate, verified, extract_ok = self._ground_candidate(cleaned)
            if verified:
                page_verified += 1
            if not extract_ok:
                extraction_failed += 1
            opportunity = self._create_draft(grounded_candidate, actor, page_verified=verified)
            imported.append(opportunity.id)
        return OpportunityDiscoverImportResult(
            imported=len(imported),
            skipped=skipped,
            opportunity_ids=imported,
            published=False,
            page_verified=page_verified,
            extraction_failed=extraction_failed,
        )

    def _ground_candidate(
        self,
        candidate: OpportunityDiscoverCandidate,
    ) -> tuple[OpportunityDiscoverCandidate, bool, bool]:
        """Fetch the official page and extract fields. Search results are never source of truth."""
        if not extraction_enabled(self.settings):
            return candidate, False, True
        try:
            page = fetch_public_page(
                candidate.application_url,
                max_text_chars=self.settings.opportunity_ai_extraction_max_chars,
            )
        except HTTPException as exc:
            logger.info("Discovery grounding fetch skipped for %s: %s", candidate.application_url, exc.detail)
            return candidate.model_copy(update={"page_verified": False}), False, False

        extracted = extract_from_page_text(
            page.text,
            page_url=page.final_url,
            settings=self.settings,
            hint_title=candidate.title,
            hint_organization=candidate.organization_name,
            hint_type=candidate.opportunity_type,
        )
        if extracted is None or extracted.confidence < 0.55:
            return (
                candidate.model_copy(
                    update={
                        "page_verified": True,
                        "source_url": candidate.source_url or page.final_url,
                        "ai_confidence": extracted.confidence if extracted else None,
                    }
                ),
                True,
                extracted is not None,
            )

        raw = RawOpportunity(
            external_id=_external_id(candidate.application_url),
            title=candidate.title,
            organization_name=candidate.organization_name,
            description=candidate.description,
            application_url=candidate.application_url,
            source_url=candidate.source_url or page.final_url,
            location=candidate.location,
            deadline=candidate.deadline,
            opportunity_type=(
                OpportunityType(candidate.opportunity_type)
                if candidate.opportunity_type in ALLOWED_TYPES
                else None
            ),
        )
        merged = merge_raw_with_extraction(raw, extracted)
        opp_type = merged.opportunity_type.value if merged.opportunity_type else candidate.opportunity_type
        return (
            OpportunityDiscoverCandidate(
                title=(merged.title or candidate.title)[:255],
                organization_name=(merged.organization_name or candidate.organization_name)[:255],
                opportunity_type=opp_type,
                application_url=candidate.application_url,
                source_url=(merged.source_url or page.final_url)[:500] if (merged.source_url or page.final_url) else None,
                description=(merged.description or candidate.description)[:4000],
                why_relevant=candidate.why_relevant,
                location=(merged.location or candidate.location)[:255],
                deadline=merged.deadline or candidate.deadline,
                career_path_slugs=candidate.career_path_slugs,
                already_imported=candidate.already_imported,
                source_host=hostname_of(candidate.application_url),
                page_verified=True,
                ai_confidence=extracted.confidence,
            ),
            True,
            True,
        )

    def _create_draft(
        self,
        candidate: OpportunityDiscoverCandidate,
        actor: User,
        *,
        page_verified: bool = False,
    ) -> Opportunity:
        opportunity_type = OpportunityType(candidate.opportunity_type)
        raw = RawOpportunity(
            external_id=_external_id(candidate.application_url),
            title=candidate.title,
            organization_name=candidate.organization_name,
            description=candidate.description,
            application_url=candidate.application_url,
            source_url=candidate.source_url,
            location=candidate.location,
            deadline=candidate.deadline,
            opportunity_type=opportunity_type,
        )
        relevance = score_relevance(raw, "medium")
        path_ids = _ids_for_slugs(
            self.db,
            CareerPath,
            candidate.career_path_slugs or relevance.career_path_slugs,
        )
        skill_ids = _ids_for_slugs(self.db, Skill, relevance.skill_slugs)
        notes = f"AI discovery draft. {candidate.why_relevant}".strip()
        if page_verified:
            notes = f"{notes} Page-verified against official URL.".strip()
        created = self.opportunities.create(
            OpportunityCreate(
                title=candidate.title,
                organization_name=candidate.organization_name,
                description=candidate.description[:20000],
                opportunity_type=opportunity_type,
                employment_type=(
                    EmploymentType.INTERNSHIP if opportunity_type == OpportunityType.INTERNSHIP else None
                ),
                experience_level=(
                    ExperienceLevel.INTERN
                    if opportunity_type == OpportunityType.INTERNSHIP
                    else ExperienceLevel.NOT_SPECIFIED
                ),
                location=candidate.location or "",
                workplace_type=relevance.workplace_type,
                application_url=candidate.application_url,
                source_url=candidate.source_url,
                deadline=candidate.deadline,
                admin_notes=notes[:4000],
                career_path_ids=path_ids,
                skill_ids=skill_ids,
            ),
            actor,
        )
        opportunity = self.db.get(Opportunity, created.id)
        assert opportunity is not None
        opportunity.trust_status = OpportunityTrustStatus.REVIEW_REQUIRED
        opportunity.external_id = _external_id(candidate.application_url)
        opportunity.relevance_score = relevance.score
        if candidate.ai_confidence is not None:
            opportunity.trust_score = Decimal(str(round(candidate.ai_confidence * 100, 2)))
        opportunity.review_assist = {
            **(opportunity.review_assist or {}),
            "page_grounding": {
                "verified": page_verified,
                "confidence": candidate.ai_confidence,
                "source_url": candidate.source_url or candidate.application_url,
            },
        }
        self.db.commit()
        return opportunity

    def _sanitize(
        self,
        row: dict | OpportunityDiscoverCandidate,
        selected: list[OpportunityType],
        seen: set[str],
    ) -> tuple[OpportunityDiscoverCandidate | None, str | None]:
        data = row if isinstance(row, dict) else row.model_dump()
        title = str(data.get("title") or "").strip()
        organization = str(data.get("organization_name") or "").strip()
        url = str(data.get("application_url") or data.get("url") or "").strip()
        if len(title) < 3 or len(organization) < 2 or not url:
            return None, "incomplete"
        if is_off_mission_title(title):
            return None, "off_mission"
        try:
            url = validate_http_url(url, "application_url")
        except HTTPException:
            return None, "invalid_url"
        if not url.lower().startswith("https://"):
            return None, "https_required"
        if is_aggregator_url(url) or is_shortened_url(url):
            return None, "aggregator"
        key = _normalize_url(url)
        if key in seen:
            return None, "duplicate"
        suggested = str(data.get("opportunity_type") or "").strip().lower()
        selected_values = {item.value for item in selected}
        inferred = infer_opportunity_type(
            RawOpportunity(
                external_id=key,
                title=title,
                organization_name=organization,
                description=str(data.get("description") or ""),
                application_url=url,
                opportunity_type=OpportunityType(suggested) if suggested in ALLOWED_TYPES else None,
            )
        )
        # Prefer an explicit type the admin selected when the model names one.
        if suggested in selected_values:
            inferred = OpportunityType(suggested)
        elif inferred not in selected:
            return None, "not_selected"
        already = self._find_by_url(url) is not None
        deadline = _parse_deadline(data.get("deadline"))
        source_url = str(data.get("source_url") or "").strip() or None
        if source_url:
            try:
                source_url = validate_http_url(source_url, "source_url")
            except HTTPException:
                source_url = None
            if source_url and (is_aggregator_url(source_url) or is_shortened_url(source_url)):
                source_url = None
        paths = [str(item) for item in (data.get("career_path_slugs") or []) if isinstance(item, str)]
        return (
            OpportunityDiscoverCandidate(
                title=title[:255],
                organization_name=organization[:255],
                opportunity_type=inferred.value,
                application_url=url[:500],
                source_url=(source_url[:500] if source_url else None),
                description=str(data.get("description") or why_or_empty(data))[:4000],
                why_relevant=str(data.get("why_relevant") or "")[:500],
                location=str(data.get("location") or "")[:255],
                deadline=deadline,
                career_path_slugs=paths[:6],
                already_imported=already,
                source_host=hostname_of(url),
                page_verified=bool(data.get("page_verified")),
                ai_confidence=(
                    float(data["ai_confidence"])
                    if isinstance(data.get("ai_confidence"), (int, float))
                    else None
                ),
            ),
            None,
        )

    def _find_by_url(self, url: str) -> Opportunity | None:
        return self.db.scalar(
            select(Opportunity).where(Opportunity.application_url == url.strip().rstrip("/"))
        ) or self.db.scalar(select(Opportunity).where(Opportunity.application_url == url.strip()))

    def _complete(
        self,
        types: list[OpportunityType],
        query: str,
        path_slugs: list[str],
    ) -> tuple[list[dict], bool, str]:
        payload = {
            "types": [item.value for item in types],
            "extra_query": query or None,
            "career_paths": path_slugs,
            "preferred_hosts": list(PREFERRED_HOSTS),
            "do_not_use_hosts": [
                "linkedin.com",
                "indeed.com",
                "web3.career",
                "crypto.jobs",
                "glassdoor.com",
                "wellfound.com",
            ],
            "mission": (
                "Analytic Sages teaches blockchain analytics, data engineering, applied AI, "
                "agentic systems, quantitative research, and forensic analytics. Prefer "
                "crypto/Web3 and blockchain-adjacent roles and programmes that match those "
                "skills. Also include strong non-Web3 data/AI/quant roles when relevant. "
                "Exclude sales, recruiting, HR, community management, and generic marketing."
            ),
        }
        instructions = (
            "You find CURRENT jobs, internships, fellowships, hackathons, grants, bounties, "
            "and research opportunities for Analytic Sages admins. Never decide to publish. "
            "Return JSON {candidates:[{title, organization_name, opportunity_type, "
            "application_url, source_url, description, why_relevant, location, deadline, "
            "career_path_slugs}]}. opportunity_type must be one of job, internship, fellowship, "
            "hackathon, grant, bounty, research. Prefer blockchain/crypto/Web3 and niche "
            "data-engineering, onchain analytics, AI, and quant roles. application_url must "
            "be an https official page (company careers, ATS posting, or program apply page), "
            "not an aggregator. Prefer preferred_hosts. Skip closed or unverifiable listings. "
            "Max 3 per type."
        )
        parsed, grounded, provider = complete_json(
            self.settings,
            instructions=instructions,
            user_content=json.dumps(payload),
            with_search=True,
        )
        rows = parsed.get("candidates") if isinstance(parsed, dict) else None
        if not isinstance(rows, list):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Discovery returned invalid JSON",
            )
        return [row for row in rows if isinstance(row, dict)][: MAX_CANDIDATES * 2], grounded, provider


def why_or_empty(data: dict) -> str:
    return str(data.get("why_relevant") or "")


def _normalize_url(url: str) -> str:
    return url.strip().rstrip("/").lower()


def _external_id(url: str) -> str:
    return "discover:" + hashlib.sha256(_normalize_url(url).encode()).hexdigest()[:24]


def _parse_deadline(value: object) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _ids_for_slugs(db: Session, model: type, slugs: list[str]) -> list[UUID]:
    if not slugs:
        return []
    rows = db.scalars(select(model).where(model.slug.in_(slugs))).all()  # type: ignore[attr-defined]
    return [row.id for row in rows]
