from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.opportunity import (
    CareerPath,
    DuplicateMatch,
    IngestionStatus,
    Opportunity,
    OpportunityCareerPath,
    OpportunityIngestion,
    OpportunityPublicBadge,
    OpportunityRiskFlag,
    OpportunitySkill,
    OpportunitySource,
    OpportunitySourceHealth,
    OpportunitySourceTrustLevel,
    OpportunitySourceType,
    OpportunityStatus,
    OpportunitySyncRun,
    OpportunityTrustStatus,
    OpportunityType,
    RiskFlagSeverity,
    Skill,
    SyncRunStatus,
    VerificationEvent,
    VerificationEventResult,
    VerificationEventType,
)
from app.models.user import User
from app.schemas.opportunities import (
    OpportunityAdminOverview,
    OpportunitySourceAdmin,
    OpportunitySourceCreate,
    OpportunitySourceList,
    OpportunitySourceUpdate,
    OpportunitySyncAllResult,
    OpportunitySyncRunPublic,
    OpportunitySyncRunList,
)
from app.services.bounty_details import upsert_bounty_details
from app.services.hackathon_details import upsert_hackathon_details
from app.services.opportunity_extract import (
    extract_from_page_text,
    extraction_enabled,
    is_incomplete_raw,
    merge_raw_with_extraction,
)
from app.services.opportunity_mission import is_off_mission_title
from app.services.opportunity_normalize import canonicalize_application_url, normalize_opportunity_fields
from app.services.opportunity_logos import resolve_organization_logo_url
from app.services.opportunity_page_fetch import fetch_public_page
from app.services.opportunity_prose import normalize_description
from app.services.opportunity_relevance import (
    RELEVANCE_REJECT_BELOW,
    normalize_title,
    score_relevance,
)
from app.services.opportunity_risk import detect_risk_flags
from app.services.opportunity_sources import RawOpportunity, get_connector
from app.services.opportunity_urls import validate_http_url
from app.services.opportunities import OpportunityService, _enum_value
from app.core.config import get_settings

logger = logging.getLogger(__name__)
CONNECTOR_SOURCE_TYPES = {
    "rss": OpportunitySourceType.RSS,
    "greenhouse": OpportunitySourceType.API,
    "ashby": OpportunitySourceType.API,
    "lever": OpportunitySourceType.API,
    "ethglobal": OpportunitySourceType.HACKATHON_PLATFORM,
    "colosseum": OpportunitySourceType.HACKATHON_PLATFORM,
    "devpost": OpportunitySourceType.HACKATHON_PLATFORM,
    "devfolio": OpportunitySourceType.HACKATHON_PLATFORM,
    "dorahacks": OpportunitySourceType.HACKATHON_PLATFORM,
    "encode": OpportunitySourceType.HACKATHON_PLATFORM,
    "superteam": OpportunitySourceType.COMMUNITY,
    "manual": OpportunitySourceType.MANUAL,
}


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _content_hash(raw: RawOpportunity) -> str:
    blob = "|".join(
        [raw.external_id, raw.title, raw.organization_name, raw.description, raw.application_url]
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _normalize_url(url: str) -> str:
    return url.strip().rstrip("/").lower()


class OpportunityIngestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.opportunities = OpportunityService(db)

    def _source_admin(self, source: OpportunitySource) -> OpportunitySourceAdmin:
        latest = self.db.scalar(
            select(OpportunitySyncRun)
            .where(OpportunitySyncRun.source_id == source.id)
            .order_by(OpportunitySyncRun.started_at.desc())
            .limit(1)
        )
        return OpportunitySourceAdmin(
            id=source.id,
            name=source.name,
            website_url=source.website_url,
            base_url=source.base_url,
            source_type=_enum_value(source.source_type),
            trust_level=_enum_value(source.trust_level),
            automation_enabled=source.automation_enabled,
            auto_publish_allowed=False,
            connector_type=source.connector_type,
            config=source.config or {},
            sync_frequency_hours=source.sync_frequency_hours,
            attribution_required=source.attribution_required,
            admin_notes=source.admin_notes or "",
            search_profiles=list(source.search_profiles or []),
            source_role=_enum_value(getattr(source, "source_role", None)) or "direct",
            capabilities=dict(getattr(source, "capabilities", None) or {}),
            last_checked_at=source.last_checked_at,
            last_success_at=source.last_success_at,
            last_failure_at=source.last_failure_at,
            last_error=source.last_error,
            health_status=_enum_value(source.health_status),
            is_active=source.is_active,
            latest_sync=self._run_public(latest) if latest else None,
            published_count=self._source_status_count(source.id, OpportunityStatus.PUBLISHED),
            rejected_count=self._source_status_count(source.id, OpportunityStatus.REJECTED),
            review_count=int(
                self.db.scalar(
                    select(func.count())
                    .select_from(Opportunity)
                    .where(
                        Opportunity.source_id == source.id,
                        Opportunity.status == OpportunityStatus.DRAFT,
                        Opportunity.trust_status.in_(
                            (OpportunityTrustStatus.REVIEW_REQUIRED, OpportunityTrustStatus.HIGH_RISK)
                        ),
                    )
                )
                or 0
            ),
            created_at=source.created_at,
            updated_at=source.updated_at,
        )

    def _source_status_count(self, source_id: UUID, status_filter: OpportunityStatus) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(Opportunity)
                .where(Opportunity.source_id == source_id, Opportunity.status == status_filter)
            )
            or 0
        )

    def _run_public(self, run: OpportunitySyncRun) -> OpportunitySyncRunPublic:
        return OpportunitySyncRunPublic(
            id=run.id,
            source_id=run.source_id,
            started_at=run.started_at,
            completed_at=run.completed_at,
            status=_enum_value(run.status),
            found=run.found,
            created=run.created,
            updated=run.updated,
            duplicates=run.duplicates,
            rejected=run.rejected,
            error_message=run.error_message,
            triggered_by=run.triggered_by,
        )

    def _get_source(self, source_id: UUID) -> OpportunitySource:
        source = self.db.get(OpportunitySource, source_id)
        if not source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
        return source

    def _sanitize_config(self, connector_type: str, config: dict) -> dict:
        if connector_type == "rss":
            feed_url = str(config.get("feed_url") or "").strip()
            if not feed_url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="RSS sources require config.feed_url",
                )
            return {"feed_url": validate_http_url(feed_url, "feed_url")}
        if connector_type == "greenhouse":
            board_token = str(config.get("board_token") or "").strip()
            if not board_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Greenhouse sources require config.board_token",
                )
            from app.services.opportunity_sources.greenhouse import BOARD_TOKEN_RE

            if not BOARD_TOKEN_RE.fullmatch(board_token):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Greenhouse board_token must be alphanumeric",
                )
            return {"board_token": board_token}
        if connector_type in {"ashby", "lever"}:
            board_token = str(config.get("board_token") or "").strip()
            label = "Ashby" if connector_type == "ashby" else "Lever"
            if not board_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{label} sources require config.board_token",
                )
            from app.services.opportunity_sources.greenhouse import BOARD_TOKEN_RE

            if not BOARD_TOKEN_RE.fullmatch(board_token):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{label} board_token must be alphanumeric",
                )
            return {"board_token": board_token}
        if connector_type == "ethglobal":
            from app.services.opportunity_sources.ethglobal import DEFAULT_EVENTS_URL, sanitize_events_url

            events_url = str(config.get("events_url") or DEFAULT_EVENTS_URL).strip()
            return {"events_url": sanitize_events_url(events_url)}
        if connector_type == "colosseum":
            from app.services.opportunity_sources.colosseum import DEFAULT_LISTING_URL, sanitize_listing_url

            listing_url = str(config.get("listing_url") or DEFAULT_LISTING_URL).strip()
            return {"listing_url": sanitize_listing_url(listing_url)}
        if connector_type == "devpost":
            from app.services.opportunity_sources.devpost import DEFAULT_LISTING_URL, sanitize_listing_url

            listing_url = str(config.get("listing_url") or DEFAULT_LISTING_URL).strip()
            return {"listing_url": sanitize_listing_url(listing_url)}
        if connector_type == "devfolio":
            from app.services.opportunity_sources.devfolio import DEFAULT_LISTING_URL, sanitize_listing_url

            listing_url = str(config.get("listing_url") or DEFAULT_LISTING_URL).strip()
            return {"listing_url": sanitize_listing_url(listing_url)}
        if connector_type == "dorahacks":
            from app.services.opportunity_sources.dorahacks import DEFAULT_LISTING_URL, sanitize_listing_url

            listing_url = str(config.get("listing_url") or DEFAULT_LISTING_URL).strip()
            return {"listing_url": sanitize_listing_url(listing_url)}
        if connector_type == "encode":
            from app.services.opportunity_sources.encode import DEFAULT_LISTING_URL, sanitize_listing_url

            listing_url = str(config.get("listing_url") or DEFAULT_LISTING_URL).strip()
            return {"listing_url": sanitize_listing_url(listing_url)}
        if connector_type == "superteam":
            from app.services.opportunity_sources.superteam import DEFAULT_LISTING_URL, sanitize_listing_url

            listing_url = str(config.get("listing_url") or DEFAULT_LISTING_URL).strip()
            return {"listing_url": sanitize_listing_url(listing_url)}
        if connector_type == "manual":
            return dict(config or {})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported connector type",
        )

    def list_sources(self) -> OpportunitySourceList:
        rows = self.db.scalars(select(OpportunitySource).order_by(OpportunitySource.name)).all()
        return OpportunitySourceList(items=[self._source_admin(row) for row in rows], total=len(rows))

    def get_source(self, source_id: UUID) -> OpportunitySourceAdmin:
        return self._source_admin(self._get_source(source_id))

    def create_source(self, payload: OpportunitySourceCreate) -> OpportunitySourceAdmin:
        connector_type = payload.connector_type
        if connector_type not in CONNECTOR_SOURCE_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported connector type")
        existing = self.db.scalar(select(OpportunitySource).where(OpportunitySource.name == payload.name.strip()))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A source with this name already exists")
        website_url = payload.website_url.strip() if payload.website_url else None
        if website_url:
            website_url = validate_http_url(website_url, "website_url")
        source = OpportunitySource(
            name=payload.name.strip(),
            website_url=website_url,
            base_url=payload.base_url.strip() if payload.base_url else None,
            source_type=CONNECTOR_SOURCE_TYPES[connector_type],
            trust_level=payload.trust_level,
            automation_enabled=payload.automation_enabled,
            auto_publish_allowed=False,
            connector_type=connector_type,
            config=self._sanitize_config(connector_type, payload.config),
            sync_frequency_hours=payload.sync_frequency_hours,
            attribution_required=payload.attribution_required,
            admin_notes=payload.admin_notes or "",
            search_profiles=payload.search_profiles or [],
            is_active=payload.is_active,
            health_status=OpportunitySourceHealth.UNKNOWN,
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return self._source_admin(source)

    def update_source(self, source_id: UUID, payload: OpportunitySourceUpdate) -> OpportunitySourceAdmin:
        source = self._get_source(source_id)
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and data["name"] is not None:
            name = data["name"].strip()
            clash = self.db.scalar(
                select(OpportunitySource).where(OpportunitySource.name == name, OpportunitySource.id != source.id)
            )
            if clash:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A source with this name already exists")
            source.name = name
        if "website_url" in data:
            website_url = (data["website_url"] or "").strip() or None
            source.website_url = validate_http_url(website_url, "website_url") if website_url else None
        if "trust_level" in data and data["trust_level"] is not None:
            source.trust_level = data["trust_level"]
        if "automation_enabled" in data and data["automation_enabled"] is not None:
            source.automation_enabled = data["automation_enabled"]
        # Trust-first: ignore attempts to enable auto-publish.
        if "auto_publish_allowed" in data:
            source.auto_publish_allowed = False
        if "is_active" in data and data["is_active"] is not None:
            source.is_active = data["is_active"]
        if "sync_frequency_hours" in data and data["sync_frequency_hours"] is not None:
            source.sync_frequency_hours = data["sync_frequency_hours"]
        if "attribution_required" in data and data["attribution_required"] is not None:
            source.attribution_required = data["attribution_required"]
        if "admin_notes" in data and data["admin_notes"] is not None:
            source.admin_notes = data["admin_notes"]
        if "base_url" in data:
            base = (data["base_url"] or "").strip() or None
            source.base_url = validate_http_url(base, "base_url") if base else None
        if "search_profiles" in data and data["search_profiles"] is not None:
            source.search_profiles = data["search_profiles"]
        if "config" in data and data["config"] is not None:
            source.config = self._sanitize_config(source.connector_type, data["config"])
        self.db.commit()
        self.db.refresh(source)
        return self._source_admin(source)

    def list_sync_runs(self, source_id: UUID, *, limit: int = 20) -> OpportunitySyncRunList:
        self._get_source(source_id)
        rows = self.db.scalars(
            select(OpportunitySyncRun)
            .where(OpportunitySyncRun.source_id == source_id)
            .order_by(OpportunitySyncRun.started_at.desc())
            .limit(limit)
        ).all()
        return OpportunitySyncRunList(items=[self._run_public(row) for row in rows], total=len(rows))

    def overview(self) -> OpportunityAdminOverview:
        now = _utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        def _count(*filters) -> int:
            query = select(func.count()).select_from(Opportunity)
            if filters:
                query = query.where(*filters)
            return int(self.db.scalar(query) or 0)

        return OpportunityAdminOverview(
            published=_count(Opportunity.status == OpportunityStatus.PUBLISHED),
            draft=_count(Opportunity.status == OpportunityStatus.DRAFT),
            review=_count(
                Opportunity.status == OpportunityStatus.DRAFT,
                Opportunity.trust_status.in_(
                    (OpportunityTrustStatus.REVIEW_REQUIRED, OpportunityTrustStatus.HIGH_RISK)
                ),
            ),
            rejected=_count(Opportunity.status == OpportunityStatus.REJECTED),
            expired=_count(Opportunity.status == OpportunityStatus.EXPIRED),
            ingested_today=_count(
                Opportunity.is_manual.is_(False),
                Opportunity.created_at >= today_start,
            ),
        )

    def sync_enabled_sources(
        self,
        actor: User | None = None,
        *,
        source_ids: list[UUID] | None = None,
    ) -> list[OpportunitySyncRunPublic]:
        stmt = select(OpportunitySource).where(
            OpportunitySource.is_active.is_(True),
            OpportunitySource.automation_enabled.is_(True),
            OpportunitySource.connector_type.in_(tuple(CONNECTOR_SOURCE_TYPES)),
            OpportunitySource.connector_type != "manual",
        )
        if source_ids:
            stmt = stmt.where(OpportunitySource.id.in_(source_ids))
        sources = self.db.scalars(stmt).all()
        return [self.sync_source(source.id, actor=actor) for source in sources]

    def sync_all_enabled(
        self,
        actor: User | None = None,
        *,
        source_ids: list[UUID] | None = None,
    ) -> OpportunitySyncAllResult:
        running = self.db.scalar(
            select(func.count())
            .select_from(OpportunitySyncRun)
            .where(OpportunitySyncRun.status == SyncRunStatus.RUNNING)
        )
        if int(running or 0) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An opportunity sync is already running. Wait for it to finish.",
            )
        runs = self.sync_enabled_sources(actor=actor, source_ids=source_ids)
        return OpportunitySyncAllResult(
            runs=runs,
            sources=len(runs),
            found=sum(run.found for run in runs),
            created=sum(run.created for run in runs),
            updated=sum(run.updated for run in runs),
            duplicates=sum(run.duplicates for run in runs),
            rejected=sum(run.rejected for run in runs),
            failed=sum(1 for run in runs if run.status == "failed"),
            published=False,
        )

    def sync_source(
        self,
        source_id: UUID,
        *,
        actor: User | None = None,
        items: list[RawOpportunity] | None = None,
    ) -> OpportunitySyncRunPublic:
        source = self._get_source(source_id)
        if source.connector_type not in CONNECTOR_SOURCE_TYPES or source.connector_type == "manual":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This source cannot be synced automatically",
            )
        running = self.db.scalar(
            select(func.count())
            .select_from(OpportunitySyncRun)
            .where(
                OpportunitySyncRun.source_id == source.id,
                OpportunitySyncRun.status == SyncRunStatus.RUNNING,
            )
        )
        if int(running or 0) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This source is already syncing. Wait for it to finish.",
            )
        run = OpportunitySyncRun(
            source_id=source.id,
            status=SyncRunStatus.RUNNING,
            triggered_by=actor.id if actor else None,
        )
        self.db.add(run)
        self.db.flush()
        try:
            fetched = items if items is not None else get_connector(source).fetch(source)
            run.found = len(fetched)
            for raw in fetched:
                try:
                    outcome = self._ingest_item(source, raw)
                except HTTPException:
                    run.rejected += 1
                    continue
                if outcome == "created":
                    run.created += 1
                elif outcome == "updated":
                    run.updated += 1
                elif outcome == "duplicate":
                    run.duplicates += 1
                else:
                    run.rejected += 1
            run.status = SyncRunStatus.COMPLETED
            run.completed_at = _utcnow()
            source.last_checked_at = run.completed_at
            source.last_success_at = run.completed_at
            source.last_error = None
            source.health_status = OpportunitySourceHealth.HEALTHY
            self.db.commit()
            self.db.refresh(run)
            return self._run_public(run)
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else "Sync failed"
            self.db.rollback()
            return self._record_failed_run(source_id, actor, detail)
        except Exception:
            logger.exception("Opportunity sync failed for source %s", source_id)
            self.db.rollback()
            return self._record_failed_run(source_id, actor, "Sync failed")

    def _record_failed_run(
        self, source_id: UUID, actor: User | None, detail: str
    ) -> OpportunitySyncRunPublic:
        source = self._get_source(source_id)
        run = OpportunitySyncRun(
            source_id=source.id,
            status=SyncRunStatus.FAILED,
            completed_at=_utcnow(),
            error_message=detail,
            triggered_by=actor.id if actor else None,
        )
        self.db.add(run)
        source.last_checked_at = run.completed_at
        source.last_failure_at = run.completed_at
        source.last_error = detail
        source.health_status = OpportunitySourceHealth.DOWN
        self.db.commit()
        self.db.refresh(run)
        return self._run_public(run)

    def _ingest_item(self, source: OpportunitySource, raw: RawOpportunity) -> str:
        raw = self._maybe_enrich_with_extraction(raw)
        title = (raw.title or "").strip()[:255]
        if not title:
            return "rejected"
        organization_name = (raw.organization_name or source.name).strip()[:255]
        source_html = ""
        if isinstance(raw.raw_data, dict):
            source_html = str(raw.raw_data.get("source_html") or "")[:20000]
        description = normalize_description(raw.description or source_html)[:20000]
        application_url = (raw.application_url or "").strip()
        hashed = _content_hash(raw)
        ingestion = OpportunityIngestion(
            source_id=source.id,
            external_id=raw.external_id[:255] if raw.external_id else None,
            raw_title=title,
            raw_content=(source_html or raw.description or "")[:20000],
            raw_data=raw.raw_data or {},
            source_url=(raw.source_url or application_url or None),
            content_hash=hashed,
            fetched_at=_utcnow(),
            processing_status=IngestionStatus.PENDING,
        )
        self.db.add(ingestion)
        self.db.flush()

        if not application_url:
            ingestion.processing_status = IngestionStatus.REJECTED
            ingestion.error_message = "Missing application URL"
            return "rejected"
        if is_off_mission_title(title):
            ingestion.processing_status = IngestionStatus.REJECTED
            ingestion.error_message = "Title is outside Analytic Sages career paths"
            return "rejected"
        try:
            application_url = validate_http_url(application_url, "application_url")
        except HTTPException as exc:
            ingestion.processing_status = IngestionStatus.REJECTED
            ingestion.error_message = exc.detail if isinstance(exc.detail, str) else "Invalid application URL"
            return "rejected"

        existing = None
        if raw.external_id:
            existing = self.db.scalar(
                select(Opportunity)
                .options(selectinload(Opportunity.risk_flags))
                .where(
                    Opportunity.source_id == source.id,
                    Opportunity.external_id == raw.external_id,
                )
            )
        if existing:
            ingestion.opportunity_id = existing.id
            ingestion.processing_status = IngestionStatus.DUPLICATE
            if existing.content_hash == hashed or existing.status in {
                OpportunityStatus.ARCHIVED,
                OpportunityStatus.REJECTED,
            }:
                return "duplicate"
            self._refresh_existing(existing, raw, application_url, hashed)
            if existing.opportunity_type in {OpportunityType.HACKATHON, OpportunityType.CHALLENGE} or (
                raw.opportunity_type in {OpportunityType.HACKATHON, OpportunityType.CHALLENGE}
            ):
                upsert_hackathon_details(existing, raw)
            if existing.opportunity_type == OpportunityType.BOUNTY or raw.opportunity_type == OpportunityType.BOUNTY:
                if existing.opportunity_type != OpportunityType.BOUNTY and raw.opportunity_type == OpportunityType.BOUNTY:
                    existing.opportunity_type = OpportunityType.BOUNTY
                upsert_bounty_details(existing, raw)
            ingestion.processing_status = IngestionStatus.PROCESSED
            return "updated"

        url_match = self._find_by_canonical_url(application_url) or self._find_by_url(application_url)
        if url_match:
            ingestion.opportunity_id = url_match.id
            ingestion.processing_status = IngestionStatus.DUPLICATE
            return "duplicate"

        relevance = score_relevance(raw, source.trust_level)
        flags = detect_risk_flags(raw)
        possible_duplicate = self._find_possible_duplicate(title, organization_name)
        normalized = normalize_opportunity_fields(
            title=title,
            organization_name=organization_name,
            description=description,
            application_url=application_url,
            source_url=raw.source_url,
            location=raw.location or "",
            workplace_type=relevance.workplace_type,
            employment_type=relevance.employment_type,
        )

        opportunity = Opportunity(
            slug=self.opportunities._ensure_slug(normalized.title, None),
            title=normalized.title,
            organization_name=normalized.organization_name,
            organization_logo_url=resolve_organization_logo_url(
                explicit=raw.organization_logo_url,
                source_website_url=source.website_url,
                application_url=normalized.application_url,
                source_url=raw.source_url,
            ),
            description=normalized.description,
            requirements=(raw.requirements or "")[:20000],
            location=normalized.location,
            location_raw=normalized.location_raw or None,
            country=normalized.country,
            region=normalized.region or relevance.region,
            location_scope=normalized.location_scope,
            workplace_type=normalized.workplace_type,
            employment_type=normalized.employment_type,
            opportunity_type=relevance.opportunity_type,
            application_url=normalized.application_url,
            canonical_application_url=normalized.canonical_application_url or None,
            source_url=None,
            deadline=raw.deadline,
            source_id=source.id,
            is_manual=False,
            external_id=raw.external_id[:255] if raw.external_id else None,
            content_hash=hashed,
            relevance_score=relevance.score,
            match_reasons=list(relevance.match_reasons),
            matched_career_tracks=list(relevance.matched_career_tracks),
            duplicate_of_id=possible_duplicate.id if possible_duplicate else None,
            duplicate_confidence=(
                DuplicateMatch.POSSIBLE.value if possible_duplicate else DuplicateMatch.NONE.value
            ),
            status=OpportunityStatus.DRAFT,
            trust_status=OpportunityTrustStatus.REVIEW_REQUIRED,
            public_badge=OpportunityPublicBadge.NONE,
        )
        self.db.add(opportunity)
        self.db.flush()
        if normalized.source_url:
            try:
                opportunity.source_url = validate_http_url(normalized.source_url, "source_url")
            except HTTPException:
                opportunity.source_url = None

        if possible_duplicate:
            flags.append(
                (
                    "DUPLICATE",
                    RiskFlagSeverity.MEDIUM,
                    f"Possible duplicate of {possible_duplicate.title} ({possible_duplicate.organization_name}).",
                )
            )
        for flag_type, severity, description_text in flags:
            opportunity.risk_flags.append(
                OpportunityRiskFlag(
                    flag_type=flag_type,
                    severity=severity,
                    flag_source="rule",
                    description=description_text,
                )
            )
        self._attach_taxonomy(opportunity, relevance.career_path_slugs, relevance.skill_slugs)
        if opportunity.opportunity_type in {OpportunityType.HACKATHON, OpportunityType.CHALLENGE}:
            upsert_hackathon_details(opportunity, raw)
        if opportunity.opportunity_type == OpportunityType.BOUNTY:
            upsert_bounty_details(opportunity, raw)

        high_or_critical = any(
            flag.severity in {RiskFlagSeverity.HIGH, RiskFlagSeverity.CRITICAL} for flag in opportunity.risk_flags
        )
        if high_or_critical:
            opportunity.trust_status = OpportunityTrustStatus.HIGH_RISK

        if relevance.score < Decimal(RELEVANCE_REJECT_BELOW) and not (
            raw.opportunity_type is not None and source.trust_level == OpportunitySourceTrustLevel.HIGH
        ):
            opportunity.status = OpportunityStatus.REJECTED
            ingestion.processing_status = IngestionStatus.REJECTED
            ingestion.opportunity_id = opportunity.id
            ingestion.error_message = f"Relevance score {relevance.score} below {RELEVANCE_REJECT_BELOW}"
            self._log_ingest(opportunity, "rejected", relevance, flags)
            return "rejected"

        # Trust-first: never auto-publish external listings. Always enter review.
        self._log_ingest(opportunity, "review_required", relevance, flags)

        ingestion.processing_status = IngestionStatus.PROCESSED
        ingestion.opportunity_id = opportunity.id
        return "created"

    def _maybe_enrich_with_extraction(self, raw: RawOpportunity) -> RawOpportunity:
        """When connector output is thin, fetch the official page and extract missing fields."""
        if not is_incomplete_raw(raw):
            return raw
        settings = get_settings()
        if not extraction_enabled(settings):
            return raw
        url = (raw.application_url or raw.source_url or "").strip()
        if not url:
            return raw
        try:
            page = fetch_public_page(
                url,
                max_text_chars=settings.opportunity_ai_extraction_max_chars,
                allow_aggregators=False,
            )
        except HTTPException:
            return raw
        extracted = extract_from_page_text(
            page.text,
            page_url=page.final_url,
            settings=settings,
            hint_title=raw.title,
            hint_organization=raw.organization_name,
            hint_type=raw.opportunity_type.value if raw.opportunity_type else None,
        )
        if extracted is None:
            return raw
        enriched = merge_raw_with_extraction(raw, extracted)
        if not enriched.source_url:
            enriched.source_url = page.final_url
        return enriched

    def _refresh_existing(
        self,
        opportunity: Opportunity,
        raw: RawOpportunity,
        application_url: str,
        hashed: str,
    ) -> None:
        if opportunity.is_manual:
            return
        opportunity.title = (raw.title or opportunity.title)[:255]
        opportunity.description = normalize_description(raw.description or opportunity.description)[:20000]
        opportunity.location = (raw.location or opportunity.location)[:255]
        opportunity.application_url = application_url
        opportunity.content_hash = hashed
        if not opportunity.organization_logo_url:
            opportunity.organization_logo_url = resolve_organization_logo_url(
                explicit=raw.organization_logo_url,
                source_website_url=opportunity.source.website_url if opportunity.source else None,
                application_url=application_url,
                source_url=raw.source_url,
            )

    def _find_by_url(self, url: str) -> Opportunity | None:
        target = _normalize_url(url)
        return self.db.scalar(
            select(Opportunity).where(func.lower(func.rtrim(Opportunity.application_url, "/")) == target)
        )

    def _find_by_canonical_url(self, url: str) -> Opportunity | None:
        canonical = canonicalize_application_url(url)
        if not canonical:
            return None
        return self.db.scalar(
            select(Opportunity).where(Opportunity.canonical_application_url == canonical)
        )

    def expire_past_deadlines(self, *, stale_days: int = 30) -> dict[str, int]:
        """Mark published opportunities past deadline as expired. Never deletes."""
        now = _utcnow()
        expired = 0
        rows = list(
            self.db.scalars(
                select(Opportunity).where(
                    Opportunity.status == OpportunityStatus.PUBLISHED,
                    Opportunity.deadline.is_not(None),
                    Opportunity.deadline < now,
                )
            ).all()
        )
        for row in rows:
            row.status = OpportunityStatus.EXPIRED
            expired += 1
        self.db.commit()
        return {"expired": expired, "stale_flagged": 0}

    def _find_possible_duplicate(self, title: str, organization_name: str) -> Opportunity | None:
        org = organization_name.strip().lower()
        target = normalize_title(title)
        if not org or not target:
            return None
        rows = self.db.scalars(
            select(Opportunity).where(func.lower(Opportunity.organization_name) == org)
        ).all()
        for row in rows:
            if normalize_title(row.title) == target:
                return row
        return None

    def _attach_taxonomy(self, opportunity: Opportunity, career_slugs: list[str], skill_slugs: list[str]) -> None:
        if career_slugs:
            paths = self.db.scalars(
                select(CareerPath).where(CareerPath.slug.in_(career_slugs), CareerPath.is_active.is_(True))
            ).all()
            for index, path in enumerate(paths):
                opportunity.career_path_links.append(
                    OpportunityCareerPath(
                        career_path_id=path.id,
                        is_primary=index == 0,
                        relevance_score=Decimal("1.000"),
                    )
                )
        if skill_slugs:
            skills = self.db.scalars(
                select(Skill).where(Skill.slug.in_(skill_slugs), Skill.is_active.is_(True))
            ).all()
            for skill in skills:
                opportunity.skill_links.append(OpportunitySkill(skill_id=skill.id))

    def _badge_for_source(self, source: OpportunitySource) -> OpportunityPublicBadge:
        if source.source_type == OpportunitySourceType.OFFICIAL_COMPANY:
            return OpportunityPublicBadge.OFFICIAL_SOURCE
        if source.source_type == OpportunitySourceType.PARTNER:
            return OpportunityPublicBadge.PARTNER
        return OpportunityPublicBadge.SOURCE_CHECKED

    def _log_ingest(
        self,
        opportunity: Opportunity,
        decision: str,
        relevance,
        flags: list[tuple[str, RiskFlagSeverity, str]],
    ) -> None:
        self.db.add(
            VerificationEvent(
                opportunity_id=opportunity.id,
                event_type=VerificationEventType.CREATED,
                result=VerificationEventResult.RECORDED,
                notes=f"Ingested: {decision}",
                evidence={
                    "decision": decision,
                    "relevance_score": float(relevance.score),
                    "relevance_breakdown": relevance.breakdown,
                    "match_reasons": list(getattr(relevance, "match_reasons", []) or []),
                    "matched_career_tracks": list(
                        getattr(relevance, "matched_career_tracks", []) or []
                    ),
                    "flags": [flag[0] for flag in flags],
                },
            )
        )
