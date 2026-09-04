from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.opportunity import (
    BountyCategory,
    EmploymentType,
    ExperienceLevel,
    HackathonEventFormat,
    LocationRegion,
    OpportunityPublicBadge,
    OpportunitySourceTrustLevel,
    OpportunityStatus,
    OpportunityTrustStatus,
    OpportunityType,
    WorkplaceType,
)

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class CareerPathPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str = ""
    is_primary: bool = False
    relevance_score: float | None = None


class SkillPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    category: str = "general"
    importance: str = "medium"


class SourcePublic(BaseModel):
    id: UUID | None = None
    name: str
    source_type: str


class HackathonDetailsPublic(BaseModel):
    short_description: str | None = None
    registration_url: str | None = None
    website_url: str | None = None
    registration_open_at: datetime | None = None
    registration_deadline: datetime | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    submission_deadline: datetime | None = None
    event_format: str = "unknown"
    prize_pool_amount: Decimal | None = None
    prize_currency: str | None = None
    prize_pool_raw: str | None = None
    team_size_min: int | None = None
    team_size_max: int | None = None
    tags: list[str] = Field(default_factory=list)
    tracks: list[str] = Field(default_factory=list)
    derived_phase: str | None = None
    registration_closes_in_days: int | None = None


class HackathonDetailsWrite(BaseModel):
    short_description: str | None = Field(default=None, max_length=500)
    registration_url: str | None = Field(default=None, max_length=500)
    website_url: str | None = Field(default=None, max_length=500)
    registration_open_at: datetime | None = None
    registration_deadline: datetime | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    submission_deadline: datetime | None = None
    event_format: HackathonEventFormat = HackathonEventFormat.UNKNOWN
    prize_pool_amount: Decimal | None = None
    prize_currency: str | None = Field(default=None, max_length=8)
    prize_pool_raw: str | None = Field(default=None, max_length=255)
    team_size_min: int | None = Field(default=None, ge=1, le=50)
    team_size_max: int | None = Field(default=None, ge=1, le=50)
    team_required: bool = False
    individual_allowed: bool = True
    tags: list[str] = Field(default_factory=list, max_length=20)
    tracks: list[str] = Field(default_factory=list, max_length=20)
    technology_focus: str | None = Field(default=None, max_length=255)


class BountyDetailsPublic(BaseModel):
    short_description: str | None = None
    listing_url: str | None = None
    reward_amount: Decimal | None = None
    reward_token: str | None = None
    reward_currency: str | None = None
    reward_raw: str | None = None
    category: str = "unknown"
    opens_at: datetime | None = None
    deadline: datetime | None = None
    winners_announced: bool = False
    skills: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    chain_focus: str | None = None
    derived_phase: str | None = None
    closes_in_days: int | None = None


class BountyDetailsWrite(BaseModel):
    short_description: str | None = Field(default=None, max_length=500)
    listing_url: str | None = Field(default=None, max_length=500)
    reward_amount: Decimal | None = None
    reward_token: str | None = Field(default=None, max_length=32)
    reward_currency: str | None = Field(default=None, max_length=8)
    reward_raw: str | None = Field(default=None, max_length=255)
    reward_min: Decimal | None = None
    reward_max: Decimal | None = None
    category: BountyCategory = BountyCategory.UNKNOWN
    opens_at: datetime | None = None
    deadline: datetime | None = None
    winners_announced: bool = False
    skills: list[str] = Field(default_factory=list, max_length=20)
    tags: list[str] = Field(default_factory=list, max_length=20)
    chain_focus: str | None = Field(default=None, max_length=120)


class OpportunityCardPublic(BaseModel):
    id: UUID
    slug: str
    title: str
    organization_name: str
    organization_logo_url: str | None = None
    compensation_text: str | None = None
    opportunity_type: str
    employment_type: str | None = None
    experience_level: str
    location: str
    location_raw: str | None = None
    location_scope: str | None = None
    country: str | None = None
    region: str | None = None
    workplace_type: str
    deadline: datetime | None = None
    published_at: datetime | None = None
    featured: bool = False
    closing_soon: bool = False
    public_badge: str
    application_domain: str | None = None
    primary_career_path: CareerPathPublic | None = None
    skills: list[SkillPublic] = Field(default_factory=list)
    source: SourcePublic | None = None
    saved: bool = False
    applied: bool = False
    match_score: float | None = None
    hackathon: HackathonDetailsPublic | None = None
    bounty: BountyDetailsPublic | None = None


class OpportunityPublic(OpportunityCardPublic):
    description: str
    requirements: str
    responsibilities: str | None = None
    benefits: str | None = None
    application_url: str
    source_url: str | None = None
    career_paths: list[CareerPathPublic] = Field(default_factory=list)
    updated_at: datetime
    similar: list[OpportunityCardPublic] = Field(default_factory=list)


class FilterOption(BaseModel):
    value: str
    label: str
    count: int = 0


class TaxonomyOption(BaseModel):
    id: UUID
    slug: str
    name: str
    count: int = 0


class OpportunityFiltersPublic(BaseModel):
    types: list[FilterOption] = Field(default_factory=list)
    career_paths: list[TaxonomyOption] = Field(default_factory=list)
    skills: list[TaxonomyOption] = Field(default_factory=list)
    workplace_types: list[FilterOption] = Field(default_factory=list)
    experience_levels: list[FilterOption] = Field(default_factory=list)
    regions: list[FilterOption] = Field(default_factory=list)


class OpportunityListPublic(BaseModel):
    items: list[OpportunityCardPublic]
    total: int
    limit: int
    offset: int


class OpportunityWriteBase(BaseModel):
    slug: str | None = Field(default=None, min_length=3, max_length=180, pattern=SLUG_PATTERN)
    title: str = Field(min_length=3, max_length=255)
    organization_name: str = Field(min_length=2, max_length=255)
    organization_logo_url: str | None = Field(default=None, max_length=500)
    compensation_text: str | None = Field(default=None, max_length=255)
    description: str = Field(default="", max_length=20000)
    requirements: str = Field(default="", max_length=20000)
    responsibilities: str | None = Field(default=None, max_length=20000)
    benefits: str | None = Field(default=None, max_length=20000)
    opportunity_type: OpportunityType = OpportunityType.JOB
    employment_type: EmploymentType | None = None
    experience_level: ExperienceLevel = ExperienceLevel.NOT_SPECIFIED
    location: str = Field(default="", max_length=255)
    country: str | None = Field(default=None, max_length=120)
    region: LocationRegion | None = None
    workplace_type: WorkplaceType = WorkplaceType.REMOTE
    application_url: str = Field(min_length=8, max_length=500)
    source_url: str | None = Field(default=None, max_length=500)
    deadline: datetime | None = None
    source_id: UUID | None = None
    public_badge: OpportunityPublicBadge = OpportunityPublicBadge.NONE
    featured: bool = False
    admin_notes: str = Field(default="", max_length=4000)
    career_path_ids: list[UUID] = Field(default_factory=list)
    skill_ids: list[UUID] = Field(default_factory=list)
    hackathon: HackathonDetailsWrite | None = None
    bounty: BountyDetailsWrite | None = None

    @field_validator(
        "responsibilities",
        "benefits",
        "country",
        "source_url",
        "slug",
        "organization_logo_url",
        "compensation_text",
        mode="before",
    )
    @classmethod
    def _empty_to_none(cls, value: object) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    @model_validator(mode="after")
    def _trim_text(self) -> OpportunityWriteBase:
        self.title = self.title.strip()
        self.organization_name = self.organization_name.strip()
        self.description = self.description.strip()
        self.requirements = self.requirements.strip()
        self.location = self.location.strip()
        self.application_url = self.application_url.strip()
        self.admin_notes = self.admin_notes.strip()
        return self


class OpportunityCreate(OpportunityWriteBase):
    pass


class OpportunityUpdate(BaseModel):
    slug: str | None = Field(default=None, min_length=3, max_length=180, pattern=SLUG_PATTERN)
    title: str | None = Field(default=None, min_length=3, max_length=255)
    organization_name: str | None = Field(default=None, min_length=2, max_length=255)
    organization_logo_url: str | None = Field(default=None, max_length=500)
    compensation_text: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=20000)
    requirements: str | None = Field(default=None, max_length=20000)
    responsibilities: str | None = Field(default=None, max_length=20000)
    benefits: str | None = Field(default=None, max_length=20000)
    opportunity_type: OpportunityType | None = None
    employment_type: EmploymentType | None = None
    experience_level: ExperienceLevel | None = None
    location: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, max_length=120)
    region: LocationRegion | None = None
    workplace_type: WorkplaceType | None = None
    application_url: str | None = Field(default=None, min_length=8, max_length=500)
    source_url: str | None = Field(default=None, max_length=500)
    deadline: datetime | None = None
    source_id: UUID | None = None
    public_badge: OpportunityPublicBadge | None = None
    featured: bool | None = None
    admin_notes: str | None = Field(default=None, max_length=4000)
    career_path_ids: list[UUID] | None = None
    skill_ids: list[UUID] | None = None
    hackathon: HackathonDetailsWrite | None = None
    bounty: BountyDetailsWrite | None = None

    @field_validator(
        "responsibilities",
        "benefits",
        "country",
        "source_url",
        "slug",
        "organization_logo_url",
        "compensation_text",
        mode="before",
    )
    @classmethod
    def _empty_to_none(cls, value: object) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None


class OpportunityDecision(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)


class OpportunityBulkPublishRequest(BaseModel):
    opportunity_ids: list[UUID] = Field(default_factory=list, max_length=50)
    notes: str | None = Field(default=None, max_length=2000)
    include_high_risk: bool = False


class OpportunityBulkPublishSkipped(BaseModel):
    id: UUID
    title: str
    reason: str


class OpportunityBulkPublishResult(BaseModel):
    published: int = 0
    skipped: int = 0
    published_ids: list[UUID] = Field(default_factory=list)
    skipped_items: list[OpportunityBulkPublishSkipped] = Field(default_factory=list)


class CareerPathAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str
    is_active: bool
    is_primary: bool = False
    relevance_score: float | None = None


class SkillAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    category: str
    is_active: bool
    importance: str = "medium"


class SourceAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    website_url: str | None
    source_type: str
    trust_level: str
    automation_enabled: bool
    auto_publish_allowed: bool
    is_active: bool


class RiskFlagAdmin(BaseModel):
    flag_type: str
    severity: str
    description: str
    is_resolved: bool = False


class OpportunityAdmin(BaseModel):
    id: UUID
    slug: str
    title: str
    organization_name: str
    organization_logo_url: str | None = None
    compensation_text: str | None = None
    description: str
    requirements: str
    responsibilities: str | None
    benefits: str | None
    opportunity_type: str
    employment_type: str | None
    experience_level: str
    location: str
    country: str | None
    region: str | None
    workplace_type: str
    application_url: str
    source_url: str | None
    deadline: datetime | None
    published_at: datetime | None
    expires_at: datetime | None
    status: OpportunityStatus
    source_id: UUID | None
    source: SourceAdmin | None = None
    trust_score: Decimal | None
    trust_status: OpportunityTrustStatus
    public_badge: OpportunityPublicBadge
    featured: bool
    admin_notes: str
    is_manual: bool = True
    external_id: str | None = None
    relevance_score: Decimal | None = None
    match_reasons: list[str] = Field(default_factory=list)
    matched_career_tracks: list[str] = Field(default_factory=list)
    duplicate_of_id: UUID | None = None
    duplicate_confidence: str | None = None
    location_raw: str | None = None
    location_scope: str | None = None
    created_by: UUID | None
    approved_by: UUID | None
    career_paths: list[CareerPathAdmin] = Field(default_factory=list)
    skills: list[SkillAdmin] = Field(default_factory=list)
    risk_flags: list[RiskFlagAdmin] = Field(default_factory=list)
    telegram_announced_at: datetime | None = None
    review_assist: dict[str, Any] = Field(default_factory=dict)
    hackathon: HackathonDetailsPublic | None = None
    bounty: BountyDetailsPublic | None = None
    created_at: datetime
    updated_at: datetime


class OpportunityAdminList(BaseModel):
    items: list[OpportunityAdmin]
    total: int
    limit: int
    offset: int


class AdminTaxonomy(BaseModel):
    career_paths: list[CareerPathAdmin]
    skills: list[SkillAdmin]
    sources: list[SourceAdmin]


class OpportunityAdminOverview(BaseModel):
    published: int = 0
    draft: int = 0
    review: int = 0
    rejected: int = 0
    expired: int = 0
    ingested_today: int = 0


class OpportunitySyncRunPublic(BaseModel):
    id: UUID
    source_id: UUID
    started_at: datetime
    completed_at: datetime | None
    status: str
    found: int = 0
    created: int = 0
    updated: int = 0
    duplicates: int = 0
    rejected: int = 0
    error_message: str | None = None
    triggered_by: UUID | None = None


class OpportunitySyncRunList(BaseModel):
    items: list[OpportunitySyncRunPublic]
    total: int


class OpportunitySyncAllResult(BaseModel):
    runs: list[OpportunitySyncRunPublic] = Field(default_factory=list)
    sources: int = 0
    found: int = 0
    created: int = 0
    updated: int = 0
    duplicates: int = 0
    rejected: int = 0
    failed: int = 0
    published: bool = False


class OpportunitySyncRequest(BaseModel):
    source_ids: list[UUID] | None = None


class OpportunitySourceAdmin(BaseModel):
    id: UUID
    name: str
    website_url: str | None
    base_url: str | None = None
    source_type: str
    trust_level: str
    automation_enabled: bool
    auto_publish_allowed: bool = False
    connector_type: str
    config: dict[str, Any] = Field(default_factory=dict)
    sync_frequency_hours: int = 6
    attribution_required: bool = True
    admin_notes: str = ""
    search_profiles: list[Any] = Field(default_factory=list)
    source_role: str = "direct"
    capabilities: dict[str, Any] = Field(default_factory=dict)
    last_checked_at: datetime | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_error: str | None = None
    health_status: str
    is_active: bool
    latest_sync: OpportunitySyncRunPublic | None = None
    published_count: int = 0
    rejected_count: int = 0
    review_count: int = 0
    created_at: datetime
    updated_at: datetime


class OpportunitySourceList(BaseModel):
    items: list[OpportunitySourceAdmin]
    total: int


class OpportunitySourceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    website_url: str | None = Field(default=None, max_length=500)
    base_url: str | None = Field(default=None, max_length=500)
    trust_level: OpportunitySourceTrustLevel = OpportunitySourceTrustLevel.MEDIUM
    automation_enabled: bool = True
    auto_publish_allowed: bool = False
    connector_type: Literal[
        "rss",
        "greenhouse",
        "ashby",
        "lever",
        "ethglobal",
        "colosseum",
        "devpost",
        "devfolio",
        "dorahacks",
        "encode",
        "superteam",
        "manual",
    ]
    config: dict[str, Any] = Field(default_factory=dict)
    sync_frequency_hours: int = Field(default=6, ge=1, le=168)
    attribution_required: bool = True
    admin_notes: str = ""
    search_profiles: list[Any] = Field(default_factory=list)
    is_active: bool = True

    @field_validator("website_url", "base_url", mode="before")
    @classmethod
    def _empty_website(cls, value: object) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None


class OpportunitySourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    website_url: str | None = Field(default=None, max_length=500)
    base_url: str | None = Field(default=None, max_length=500)
    trust_level: OpportunitySourceTrustLevel | None = None
    automation_enabled: bool | None = None
    auto_publish_allowed: bool | None = None
    is_active: bool | None = None
    sync_frequency_hours: int | None = Field(default=None, ge=1, le=168)
    attribution_required: bool | None = None
    admin_notes: str | None = None
    search_profiles: list[Any] | None = None
    config: dict[str, Any] | None = None


class OpportunitySavePublic(BaseModel):
    id: UUID
    opportunity_id: UUID
    state: str
    closed: bool = False
    created_at: datetime
    opportunity: OpportunityCardPublic


class OpportunitySaveList(BaseModel):
    items: list[OpportunitySavePublic]
    total: int


class UserCareerInterestsPublic(BaseModel):
    career_paths: list[CareerPathPublic] = Field(default_factory=list)


class UserCareerInterestsUpdate(BaseModel):
    career_path_ids: list[UUID] = Field(default_factory=list)


class OpportunityReviewAssistPublic(BaseModel):
    configured: bool
    notes: str | None = None
    suggested_type: str | None = None
    suggested_career_paths: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    generated_at: datetime | None = None
    provider: str | None = None


class OpportunityDiscoverRequest(BaseModel):
    types: list[OpportunityType] = Field(default_factory=list)
    query: str | None = Field(default=None, max_length=200)


class OpportunityDiscoverCandidate(BaseModel):
    title: str
    organization_name: str
    opportunity_type: str
    application_url: str
    source_url: str | None = None
    description: str = ""
    why_relevant: str = ""
    location: str = ""
    deadline: datetime | None = None
    career_path_slugs: list[str] = Field(default_factory=list)
    already_imported: bool = False
    source_host: str | None = None


class OpportunityDiscoverResponse(BaseModel):
    configured: bool
    grounded: bool = False
    never_publishes: bool = True
    types_updated: int = 0
    dropped: int = 0
    candidates: list[OpportunityDiscoverCandidate] = Field(default_factory=list)
    provider: str | None = None
    notes: str | None = None


class OpportunityDiscoverImportRequest(BaseModel):
    candidates: list[OpportunityDiscoverCandidate] = Field(default_factory=list)


class OpportunityDiscoverImportResult(BaseModel):
    imported: int
    skipped: int
    opportunity_ids: list[UUID] = Field(default_factory=list)
    published: bool = False


class OpportunityReclassifyResult(BaseModel):
    updated: int
