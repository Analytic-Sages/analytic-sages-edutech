from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.enums import pg_enum
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User


class OpportunityType(str, enum.Enum):
    JOB = "job"
    INTERNSHIP = "internship"
    FELLOWSHIP = "fellowship"
    HACKATHON = "hackathon"
    GRANT = "grant"
    BOUNTY = "bounty"
    CHALLENGE = "challenge"
    RESEARCH = "research"
    OTHER = "other"


class HackathonEventFormat(str, enum.Enum):
    ONLINE = "online"
    IN_PERSON = "in_person"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


class BountyCategory(str, enum.Enum):
    BUG = "bug"
    SECURITY = "security"
    DEVELOPMENT = "development"
    CONTENT = "content"
    DESIGN = "design"
    RESEARCH = "research"
    QUEST = "quest"
    OTHER = "other"
    UNKNOWN = "unknown"


class OpportunitySourceRole(str, enum.Enum):
    DIRECT = "direct"
    DISCOVERY = "discovery"
    AGGREGATOR = "aggregator"
    MANUAL = "manual"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    VOLUNTEER = "volunteer"
    OTHER = "other"


class ExperienceLevel(str, enum.Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    NOT_SPECIFIED = "not_specified"


class WorkplaceType(str, enum.Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


class LocationScope(str, enum.Enum):
    WORLDWIDE = "worldwide"
    GLOBAL = "global"
    AFRICA = "africa"
    EUROPE = "europe"
    EMEA = "emea"
    NORTH_AMERICA = "north_america"
    US_ONLY = "us_only"
    UK_ONLY = "uk_only"
    OTHER = "other"
    UNKNOWN = "unknown"


class LocationRegion(str, enum.Enum):
    GLOBAL = "global"
    AFRICA = "africa"
    NIGERIA = "nigeria"
    EUROPE = "europe"
    NORTH_AMERICA = "north_america"
    ASIA = "asia"
    REMOTE = "remote"


class OpportunityStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class IngestionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"
    FAILED = "failed"


class SyncRunStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskFlagSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DuplicateMatch(str, enum.Enum):
    NONE = "none"
    POSSIBLE = "possible"
    CONFIRMED = "confirmed"


class OpportunityTrustStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    HIGH_CONFIDENCE = "high_confidence"
    SOURCE_CHECKED = "source_checked"
    REVIEW_REQUIRED = "review_required"
    HIGH_RISK = "high_risk"


class OpportunityPublicBadge(str, enum.Enum):
    NONE = "none"
    OFFICIAL_SOURCE = "official_source"
    PARTNER = "partner"
    SOURCE_CHECKED = "source_checked"
    COMMUNITY_SUBMISSION = "community_submission"


class OpportunitySourceType(str, enum.Enum):
    OFFICIAL_COMPANY = "official_company"
    PARTNER = "partner"
    JOB_BOARD = "job_board"
    HACKATHON_PLATFORM = "hackathon_platform"
    COMMUNITY = "community"
    MANUAL = "manual"
    API = "api"
    RSS = "rss"


class OpportunitySourceTrustLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OpportunitySourceHealth(str, enum.Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class OpportunitySkillImportance(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class OpportunitySaveState(str, enum.Enum):
    SAVED = "saved"
    APPLIED = "applied"


class VerificationEventType(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    ADMIN_APPROVAL = "admin_approval"
    ADMIN_REJECT = "admin_reject"
    ADMIN_ARCHIVE = "admin_archive"
    ADMIN_UNPUBLISH = "admin_unpublish"


class VerificationEventResult(str, enum.Enum):
    RECORDED = "recorded"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    UNPUBLISHED = "unpublished"


class CareerPath(Base):
    __tablename__ = "career_paths"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False, default="general")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class OpportunitySource(Base):
    __tablename__ = "opportunity_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_type: Mapped[OpportunitySourceType] = mapped_column(
        pg_enum(OpportunitySourceType, name="opportunity_source_type"),
        nullable=False,
        default=OpportunitySourceType.MANUAL,
    )
    trust_level: Mapped[OpportunitySourceTrustLevel] = mapped_column(
        pg_enum(OpportunitySourceTrustLevel, name="opportunity_source_trust_level"),
        nullable=False,
        default=OpportunitySourceTrustLevel.MEDIUM,
    )
    automation_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_publish_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    connector_type: Mapped[str] = mapped_column(String(80), nullable=False, default="manual")
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sync_frequency_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    attribution_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    admin_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_profiles: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    source_role: Mapped[OpportunitySourceRole] = mapped_column(
        pg_enum(OpportunitySourceRole, name="opportunity_source_role"),
        nullable=False,
        default=OpportunitySourceRole.DIRECT,
    )
    capabilities: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text(
            "'{\"supports_automation\": false, \"supports_api\": false, "
            "\"supports_rss\": false, \"supports_search\": false, "
            "\"requires_review\": true}'::jsonb"
        ),
    )
    health_status: Mapped[OpportunitySourceHealth] = mapped_column(
        pg_enum(OpportunitySourceHealth, name="opportunity_source_health"),
        nullable=False,
        default=OpportunitySourceHealth.UNKNOWN,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    ingestions: Mapped[list[OpportunityIngestion]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sync_runs: Mapped[list[OpportunitySyncRun]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    requirements: Mapped[str] = mapped_column(Text, nullable=False, default="")
    responsibilities: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefits: Mapped[str | None] = mapped_column(Text, nullable=True)
    opportunity_type: Mapped[OpportunityType] = mapped_column(
        pg_enum(OpportunityType, name="opportunity_type"),
        nullable=False,
        default=OpportunityType.JOB,
        index=True,
    )
    employment_type: Mapped[EmploymentType | None] = mapped_column(
        pg_enum(EmploymentType, name="employment_type"),
        nullable=True,
    )
    experience_level: Mapped[ExperienceLevel] = mapped_column(
        pg_enum(ExperienceLevel, name="experience_level"),
        nullable=False,
        default=ExperienceLevel.NOT_SPECIFIED,
    )
    location: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    location_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    location_scope: Mapped[LocationScope | None] = mapped_column(
        pg_enum(LocationScope, name="location_scope"),
        nullable=True,
    )
    workplace_type: Mapped[WorkplaceType] = mapped_column(
        pg_enum(WorkplaceType, name="workplace_type"),
        nullable=False,
        default=WorkplaceType.REMOTE,
        index=True,
    )
    application_url: Mapped[str] = mapped_column(String(500), nullable=False)
    canonical_application_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, index=True
    )
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[OpportunityStatus] = mapped_column(
        pg_enum(OpportunityStatus, name="opportunity_status"),
        nullable=False,
        default=OpportunityStatus.DRAFT,
        index=True,
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunity_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    trust_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    trust_status: Mapped[OpportunityTrustStatus] = mapped_column(
        pg_enum(OpportunityTrustStatus, name="opportunity_trust_status"),
        nullable=False,
        default=OpportunityTrustStatus.UNVERIFIED,
    )
    public_badge: Mapped[OpportunityPublicBadge] = mapped_column(
        pg_enum(OpportunityPublicBadge, name="opportunity_public_badge"),
        nullable=False,
        default=OpportunityPublicBadge.NONE,
    )
    featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    admin_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_manual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    relevance_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True, index=True)
    match_reasons: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    matched_career_tracks: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    duplicate_confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    duplicate_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    telegram_announced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_assist: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    source: Mapped[OpportunitySource | None] = relationship()
    creator: Mapped[User | None] = relationship(foreign_keys=[created_by])
    approver: Mapped[User | None] = relationship(foreign_keys=[approved_by])
    hackathon_details: Mapped[OpportunityHackathonDetails | None] = relationship(
        back_populates="opportunity",
        uselist=False,
        cascade="all, delete-orphan",
    )
    bounty_details: Mapped[OpportunityBountyDetails | None] = relationship(
        back_populates="opportunity",
        uselist=False,
        cascade="all, delete-orphan",
    )
    career_path_links: Mapped[list[OpportunityCareerPath]] = relationship(
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )
    skill_links: Mapped[list[OpportunitySkill]] = relationship(
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )
    verification_events: Mapped[list[VerificationEvent]] = relationship(
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )
    risk_flags: Mapped[list[OpportunityRiskFlag]] = relationship(
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )
    duplicate_of: Mapped[Opportunity | None] = relationship(remote_side="Opportunity.id")


class OpportunityHackathonDetails(Base):
    __tablename__ = "opportunity_hackathon_details"

    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    registration_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    registration_open_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    registration_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submission_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    announcement_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    event_format: Mapped[HackathonEventFormat] = mapped_column(
        pg_enum(HackathonEventFormat, name="hackathon_event_format"),
        nullable=False,
        default=HackathonEventFormat.UNKNOWN,
    )
    prize_pool_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    prize_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    prize_pool_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)
    team_size_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    team_size_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    team_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    individual_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    tags: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    tracks: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    technology_focus: Mapped[str | None] = mapped_column(String(255), nullable=True)
    derived_phase: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    opportunity: Mapped[Opportunity] = relationship(back_populates="hackathon_details")


class OpportunityBountyDetails(Base):
    __tablename__ = "opportunity_bounty_details"

    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    listing_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reward_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    reward_token: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reward_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    reward_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reward_min: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    reward_max: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    category: Mapped[BountyCategory] = mapped_column(
        pg_enum(BountyCategory, name="bounty_category"),
        nullable=False,
        default=BountyCategory.UNKNOWN,
    )
    opens_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    winners_announced: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    skills: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    tags: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    chain_focus: Mapped[str | None] = mapped_column(String(120), nullable=True)
    derived_phase: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    opportunity: Mapped[Opportunity] = relationship(back_populates="bounty_details")


class OpportunityCareerPath(Base):
    __tablename__ = "opportunity_career_paths"
    __table_args__ = (
        UniqueConstraint("opportunity_id", "career_path_id", name="uq_opportunity_career_paths"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    career_path_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_paths.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relevance_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False, default=Decimal("1.000"))
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    opportunity: Mapped[Opportunity] = relationship(back_populates="career_path_links")
    career_path: Mapped[CareerPath] = relationship()


class OpportunitySkill(Base):
    __tablename__ = "opportunity_skills"
    __table_args__ = (
        UniqueConstraint("opportunity_id", "skill_id", name="uq_opportunity_skills"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    importance: Mapped[OpportunitySkillImportance] = mapped_column(
        pg_enum(OpportunitySkillImportance, name="opportunity_skill_importance"),
        nullable=False,
        default=OpportunitySkillImportance.MEDIUM,
    )

    opportunity: Mapped[Opportunity] = relationship(back_populates="skill_links")
    skill: Mapped[Skill] = relationship()


class VerificationEvent(Base):
    __tablename__ = "verification_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[VerificationEventType] = mapped_column(
        pg_enum(VerificationEventType, name="verification_event_type"),
        nullable=False,
    )
    result: Mapped[VerificationEventResult] = mapped_column(
        pg_enum(VerificationEventResult, name="verification_event_result"),
        nullable=False,
        default=VerificationEventResult.RECORDED,
    )
    performed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    evidence: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    opportunity: Mapped[Opportunity | None] = relationship(back_populates="verification_events")
    actor: Mapped[User | None] = relationship()


class OpportunityIngestion(Base):
    __tablename__ = "opportunity_ingestions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunity_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    raw_title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    raw_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    raw_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processing_status: Mapped[IngestionStatus] = mapped_column(
        pg_enum(IngestionStatus, name="opportunity_ingestion_status"),
        nullable=False,
        default=IngestionStatus.PENDING,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    source: Mapped[OpportunitySource] = relationship(back_populates="ingestions")
    opportunity: Mapped[Opportunity | None] = relationship()


class OpportunitySyncRun(Base):
    __tablename__ = "opportunity_sync_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunity_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[SyncRunStatus] = mapped_column(
        pg_enum(SyncRunStatus, name="opportunity_sync_run_status"),
        nullable=False,
        default=SyncRunStatus.RUNNING,
        index=True,
    )
    found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    triggered_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    source: Mapped[OpportunitySource] = relationship(back_populates="sync_runs")
    actor: Mapped[User | None] = relationship()


class OpportunityRiskFlag(Base):
    __tablename__ = "opportunity_risk_flags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    flag_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    severity: Mapped[RiskFlagSeverity] = mapped_column(
        pg_enum(RiskFlagSeverity, name="opportunity_risk_flag_severity"),
        nullable=False,
        default=RiskFlagSeverity.MEDIUM,
    )
    flag_source: Mapped[str] = mapped_column(String(40), nullable=False, default="rule")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    opportunity: Mapped[Opportunity] = relationship(back_populates="risk_flags")


class OpportunitySave(Base):
    __tablename__ = "opportunity_saves"
    __table_args__ = (UniqueConstraint("user_id", "opportunity_id", name="uq_opportunity_saves_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    state: Mapped[OpportunitySaveState] = mapped_column(
        pg_enum(OpportunitySaveState, name="opportunity_save_state"),
        nullable=False,
        default=OpportunitySaveState.SAVED,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    opportunity: Mapped[Opportunity] = relationship()


class UserCareerInterest(Base):
    __tablename__ = "user_career_interests"
    __table_args__ = (
        UniqueConstraint("user_id", "career_path_id", name="uq_user_career_interests"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    career_path_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_paths.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    career_path: Mapped[CareerPath] = relationship()


class OpportunityDigestRun(Base):
    __tablename__ = "opportunity_digest_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    listing_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    item_ids: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="sent")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    triggered_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
