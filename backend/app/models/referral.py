"""Referral Partner Program models — profile, attribution, conversions, ledger, payouts."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.referrals import (
    PartnerLedgerEntryType,
    PartnerLedgerStatus,
    PartnerPayoutStatus,
    ReferralConversionStatus,
    ReferralFraudStatus,
    ReferralPartnerStatus,
)
from app.db.enums import pg_enum
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.billing import PaymentObligation
    from app.models.classroom import Cohort
    from app.models.course import Course
    from app.models.enrollment import Enrollment
    from app.models.payment import Payment
    from app.models.user import User


class ReferralPartner(Base):
    __tablename__ = "referral_partners"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    status: Mapped[ReferralPartnerStatus] = mapped_column(
        pg_enum(ReferralPartnerStatus, name="referral_partner_status"),
        nullable=False,
        default=ReferralPartnerStatus.PENDING,
        index=True,
    )
    referral_code: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    social_handle: Mapped[str | None] = mapped_column(String(160), nullable=True)
    promotion_channels: Mapped[str | None] = mapped_column(Text, nullable=True)
    terms_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    cohort_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referral_partner_cohorts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    profile_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    marketing_guidelines_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    onboarding_terms_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(foreign_keys=[user_id])


class ReferralClick(Base):
    __tablename__ = "referral_clicks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("referral_partners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    referral_link_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referral_links.id", ondelete="SET NULL"), nullable=True, index=True
    )
    referral_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    anonymous_visitor_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    landing_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class ReferralAttribution(Base):
    __tablename__ = "referral_attributions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("referral_partners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    referral_link_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referral_links.id", ondelete="SET NULL"), nullable=True, index=True
    )
    anonymous_visitor_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    referred_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    referral_code: Mapped[str] = mapped_column(String(32), nullable=False)
    landing_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    attributed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    partner: Mapped[ReferralPartner] = relationship()


class ReferralConversion(Base):
    __tablename__ = "referral_conversions"
    __table_args__ = (
        UniqueConstraint("payment_id", name="uq_referral_conversions_payment_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("referral_partners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    referral_link_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referral_links.id", ondelete="SET NULL"), nullable=True, index=True
    )
    referred_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True
    )
    cohort_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cohorts.id", ondelete="SET NULL"), nullable=True
    )
    enrollment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="SET NULL"), nullable=True
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payment_obligation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_obligations.id", ondelete="SET NULL"),
        nullable=True,
    )
    eligible_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(8, 6), nullable=False)
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[ReferralConversionStatus] = mapped_column(
        pg_enum(ReferralConversionStatus, name="referral_conversion_status"),
        nullable=False,
        default=ReferralConversionStatus.PENDING,
        index=True,
    )
    available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fraud_status: Mapped[ReferralFraudStatus] = mapped_column(
        pg_enum(ReferralFraudStatus, name="referral_fraud_status"),
        nullable=False,
        default=ReferralFraudStatus.CLEAR,
        index=True,
    )
    fraud_flags: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    reporting_fx_rate: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    reporting_fx_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reporting_usd_equivalent: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    partner: Mapped[ReferralPartner] = relationship()
    payment: Mapped[Payment] = relationship()
    course: Mapped[Course | None] = relationship()
    cohort: Mapped[Cohort | None] = relationship()


class PartnerLedgerEntry(Base):
    __tablename__ = "partner_ledger_entries"
    __table_args__ = (
        UniqueConstraint(
            "partner_id",
            "entry_type",
            "reference_type",
            "reference_id",
            name="uq_partner_ledger_ref",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("referral_partners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entry_type: Mapped[PartnerLedgerEntryType] = mapped_column(
        pg_enum(PartnerLedgerEntryType, name="partner_ledger_entry_type"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    status: Mapped[PartnerLedgerStatus] = mapped_column(
        pg_enum(PartnerLedgerStatus, name="partner_ledger_status"),
        nullable=False,
        default=PartnerLedgerStatus.PENDING,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reporting_fx_rate: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    reporting_fx_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reporting_usd_equivalent: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class PartnerPayoutRequest(Base):
    __tablename__ = "partner_payout_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("referral_partners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")
    payment_details_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[PartnerPayoutStatus] = mapped_column(
        pg_enum(PartnerPayoutStatus, name="partner_payout_status"),
        nullable=False,
        default=PartnerPayoutStatus.REQUESTED,
        index=True,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ReferralAuditEvent(Base):
    __tablename__ = "referral_audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    before_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    after_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )



class ReferralPartnerCohort(Base):
    __tablename__ = "referral_partner_cohorts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    capacity: Mapped[int] = mapped_column(nullable=False, default=10)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ReferralPartnerApplication(Base):
    __tablename__ = "referral_partner_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referral_partners.id", ondelete="SET NULL"), nullable=True
    )
    cohort_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referral_partner_cohorts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    email_normalized: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    whatsapp_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    telegram_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    social_profiles: Mapped[list[dict[str, str]]] = mapped_column(JSONB, nullable=False, default=list)
    communities: Mapped[str | None] = mapped_column(Text, nullable=True)
    audience_size: Mapped[str | None] = mapped_column(String(80), nullable=True)
    audience_engagement: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevant_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    partnership_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    interested_courses: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    promotion_channels: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    marketing_plan: Mapped[str] = mapped_column(Text, nullable=False)
    terms_accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    terms_version: Mapped[str] = mapped_column(String(40), nullable=False, default="referral-partner-v1")
    marketing_guidelines_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="submitted", index=True)
    scores: Mapped[dict[str, int]] = mapped_column(JSONB, nullable=False, default=dict)
    score_total: Mapped[int | None] = mapped_column(nullable=True)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    interview_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    interview_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    interview_reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    interview_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    interview_decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    interview_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ReferralLink(Base):
    __tablename__ = "referral_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referral_partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cohort_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cohorts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    target_type: Mapped[str] = mapped_column(String(16), nullable=False, default="general")
    target_slug: Mapped[str | None] = mapped_column(String(160), nullable=True)
    campaign_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    campaign_channel: Mapped[str | None] = mapped_column(String(80), nullable=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    destination_path: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="inactive", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    revocation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class ReferralProgramResources(Base):
    __tablename__ = "referral_program_resources"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    terms_version: Mapped[str] = mapped_column(String(40), nullable=False)
    program_overview: Mapped[str] = mapped_column(Text, nullable=False)
    commission_policy: Mapped[str] = mapped_column(Text, nullable=False)
    attribution_policy: Mapped[str] = mapped_column(Text, nullable=False)
    payout_policy: Mapped[str] = mapped_column(Text, nullable=False)
    marketing_guidelines: Mapped[str] = mapped_column(Text, nullable=False)
    support_contact: Mapped[str] = mapped_column(String(320), nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
