"""Schemas for referral-partner application, onboarding and link management."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ReferralPartnerApplicationCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=5, max_length=320)
    country: str | None = Field(default=None, max_length=100)
    timezone: str | None = Field(default=None, max_length=100)
    linkedin_url: str | None = Field(default=None, max_length=512)
    social_profiles: list[dict[str, str]] = Field(default_factory=list, max_length=10)
    communities: str | None = Field(default=None, max_length=2000)
    audience_size: str | None = Field(default=None, max_length=80)
    audience_engagement: str | None = Field(default=None, max_length=2000)
    relevant_experience: str | None = Field(default=None, max_length=3000)
    partnership_experience: str | None = Field(default=None, max_length=2000)
    interested_courses: list[str] = Field(default_factory=list, max_length=20)
    promotion_channels: list[str] = Field(min_length=1, max_length=10)
    marketing_plan: str = Field(min_length=30, max_length=3000)
    terms_accepted: bool
    terms_version: str = Field(default="referral-partner-v1", min_length=1, max_length=40)


class ReferralPartnerApplicationPublic(BaseModel):
    id: UUID
    full_name: str
    email: str
    country: str | None = None
    timezone: str | None = None
    linkedin_url: str | None = None
    social_profiles: list[dict[str, str]] = Field(default_factory=list)
    communities: str | None = None
    audience_size: str | None = None
    audience_engagement: str | None = None
    relevant_experience: str | None = None
    partnership_experience: str | None = None
    interested_courses: list[str] = Field(default_factory=list)
    promotion_channels: list[str] = Field(default_factory=list)
    marketing_plan: str
    status: str
    score_total: int | None = None
    cohort_id: UUID | None = None
    partner_id: UUID | None = None
    reviewer_id: UUID | None = None
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    interview_reviewer_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    terms_version: str
    terms_accepted_at: datetime
    review_notes: str | None = None
    rejection_reason: str | None = None
    scores: dict[str, int] = Field(default_factory=dict)
    interview_at: datetime | None = None
    interview_status: str | None = None
    interview_notes: str | None = None
    interview_decision: str | None = None
    interview_reason: str | None = None
    follow_up_actions: str | None = None

    model_config = {"from_attributes": True}


class ReferralPartnerApplicationPatch(BaseModel):
    status: str | None = None
    cohort_id: UUID | None = None
    scores: dict[str, int] | None = None
    review_notes: str | None = Field(default=None, max_length=5000)
    rejection_reason: str | None = Field(default=None, max_length=2000)
    interview_at: datetime | None = None
    interview_status: str | None = Field(default=None, max_length=32)
    interview_notes: str | None = Field(default=None, max_length=5000)
    interview_decision: str | None = Field(default=None, max_length=32)
    interview_reason: str | None = Field(default=None, max_length=2000)
    follow_up_actions: str | None = Field(default=None, max_length=2000)


class ReferralPartnerCohortCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    capacity: int = Field(default=10, ge=1, le=1000)
    is_active: bool = True


class ReferralPartnerCohortPatch(BaseModel):
    capacity: int | None = Field(default=None, ge=1, le=1000)
    is_active: bool | None = None


class ReferralPartnerCohortPublic(BaseModel):
    id: UUID
    name: str
    capacity: int
    approved_count: int = 0
    remaining_slots: int = 0
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ReferralLinkCreate(BaseModel):
    course_id: UUID | None = None
    cohort_id: UUID | None = None
    campaign_label: str | None = Field(default=None, max_length=120)
    campaign_channel: str | None = Field(default=None, max_length=80)


class ReferralLinkPublic(BaseModel):
    id: UUID
    partner_id: UUID
    course_id: UUID | None = None
    course_title: str | None = None
    course_slug: str | None = None
    cohort_id: UUID | None = None
    cohort_name: str | None = None
    target_type: str = "general"
    target_slug: str | None = None
    target_available: bool = True
    unavailable_reason: str | None = None
    campaign_label: str | None = None
    campaign_channel: str | None = None
    code: str
    destination_path: str
    url: str
    status: str
    clicks: int = 0
    paid_enrollments: int = 0
    conversion_rate: Decimal = Decimal("0.00")
    commission_amount: Decimal | None = None
    commission_currency: str | None = None
    commission_by_currency: dict[str, Decimal] = Field(default_factory=dict)
    created_at: datetime
    revoked_at: datetime | None = None


class ReferralLinkPatch(BaseModel):
    status: str | None = None
    revocation_reason: str | None = Field(default=None, max_length=1000)


class PartnerOnboardingComplete(BaseModel):
    profile_completed: bool
    terms_accepted: bool
    marketing_guidelines_accepted: bool
    terms_version: str = Field(min_length=1, max_length=40)


class ReferralProgramResourcesPublic(BaseModel):
    terms_version: str
    program_overview: str
    commission_policy: str
    attribution_policy: str
    payout_policy: str
    marketing_guidelines: str
    support_contact: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReferralProgramResourcesPatch(BaseModel):
    terms_version: str = Field(min_length=1, max_length=40)
    program_overview: str = Field(min_length=10, max_length=5000)
    commission_policy: str = Field(min_length=10, max_length=5000)
    attribution_policy: str = Field(min_length=10, max_length=5000)
    payout_policy: str = Field(min_length=10, max_length=5000)
    marketing_guidelines: str = Field(min_length=10, max_length=8000)
    support_contact: str = Field(min_length=3, max_length=320)


class ReferralAuditRow(BaseModel):
    id: UUID
    actor_id: UUID | None = None
    action: str
    entity_type: str
    entity_id: UUID | None = None
    note: str | None = None
    before_json: dict | None = None
    after_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReferralPartnerApplicationStatusPublic(BaseModel):
    id: UUID
    full_name: str
    email: str
    status: str
    cohort_id: UUID | None = None
    partner_id: UUID | None = None
    terms_version: str
    terms_accepted_at: datetime
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
