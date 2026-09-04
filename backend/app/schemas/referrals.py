from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.referrals import (
    PartnerPayoutStatus,
    ReferralConversionStatus,
    ReferralFraudStatus,
    ReferralPartnerStatus,
)


class ReferralTrackRequest(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    landing_path: str | None = Field(default=None, max_length=512)
    destination: str | None = Field(default=None, max_length=512)
    anonymous_visitor_id: str | None = Field(default=None, max_length=64)


class ReferralTrackResponse(BaseModel):
    ok: bool
    redirect_path: str
    anonymous_visitor_id: str


class PartnerApplyRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=160)
    social_handle: str | None = Field(default=None, max_length=160)
    promotion_channels: str | None = Field(default=None, max_length=500)
    terms_accepted: bool


class PartnerPublic(BaseModel):
    id: UUID
    status: ReferralPartnerStatus
    referral_code: str | None
    display_name: str
    social_handle: str | None = None
    promotion_channels: str | None = None
    created_at: datetime
    approved_at: datetime | None = None

    model_config = {"from_attributes": True}


class CurrencyBalanceRow(BaseModel):
    currency: str
    pending_commission: Decimal
    available_balance: Decimal
    total_paid_out: Decimal
    minimum_payout: Decimal
    estimated_usd_pending: Decimal | None = None
    estimated_usd_available: Decimal | None = None
    estimated_usd_paid_out: Decimal | None = None


class PartnerDashboard(BaseModel):
    clicks: int
    registrations: int
    paid_enrollments: int
    conversion_rate: float
    pending_commission: Decimal
    available_balance: Decimal
    total_paid_out: Decimal
    currency: str
    referral_code: str | None
    status: str
    display_name: str
    minimum_payout: Decimal
    commission_rate: Decimal
    hold_days: int
    referral_link: str | None = None
    balances_by_currency: list[CurrencyBalanceRow] = Field(default_factory=list)
    reporting_currency: str = "USD"
    estimated_usd_pending: Decimal | None = None
    estimated_usd_available: Decimal | None = None
    estimated_usd_paid_out: Decimal | None = None
    estimated_usd_portfolio: Decimal | None = None
    minimum_payout_thresholds: dict[str, Decimal] = Field(default_factory=dict)


class PartnerConversionRow(BaseModel):
    id: UUID
    programme: str
    learner_label: str
    eligible_amount: Decimal
    commission_amount: Decimal
    currency: str
    status: ReferralConversionStatus
    created_at: datetime
    reporting_usd_equivalent: Decimal | None = None


class PartnerPayoutRow(BaseModel):
    id: UUID
    amount: Decimal
    currency: str
    status: PartnerPayoutStatus
    requested_at: datetime
    processed_at: datetime | None = None
    admin_note: str | None = None

    model_config = {"from_attributes": True}


class PartnerPayoutCreate(BaseModel):
    amount: Decimal
    currency: str = "USD"
    payment_details_reference: str | None = Field(default=None, max_length=255)


class AdminReferralOverview(BaseModel):
    total_partners: int
    active_partners: int
    pending_applications: int
    total_clicks: int
    total_registrations: int
    total_paid_enrollments: int
    commission_pending: Decimal
    commission_available: Decimal
    commission_paid: Decimal
    currency: str
    balances_by_currency: list[CurrencyBalanceRow] = Field(default_factory=list)
    reporting_currency: str = "USD"
    estimated_usd_pending: Decimal | None = None
    estimated_usd_available: Decimal | None = None
    estimated_usd_paid_out: Decimal | None = None
    estimated_usd_portfolio: Decimal | None = None


class AdminPartnerPatch(BaseModel):
    status: ReferralPartnerStatus | None = None
    note: str | None = None
    regenerate_code: bool = False


class AdminPayoutPatch(BaseModel):
    status: PartnerPayoutStatus
    note: str | None = None


class AdminConversionRow(BaseModel):
    id: UUID
    partner_name: str
    learner_email: str
    programme: str
    payment_id: UUID
    eligible_amount: Decimal
    commission_amount: Decimal
    currency: str
    status: ReferralConversionStatus
    fraud_status: ReferralFraudStatus = ReferralFraudStatus.CLEAR
    created_at: datetime
    reporting_usd_equivalent: Decimal | None = None


class AdminAttributionOverride(BaseModel):
    referred_user_id: UUID
    partner_id: UUID
    note: str | None = Field(default=None, max_length=500)


class LeaderboardEntry(BaseModel):
    rank: int
    display_name: str
    successful_enrollments: int


class LeaderboardResponse(BaseModel):
    period: str
    entries: list[LeaderboardEntry]


class ReleaseCommissionsResponse(BaseModel):
    released: int
