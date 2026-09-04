"""Referral Partner Program enums and helpers."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from enum import Enum


class ReferralPartnerStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class ReferralConversionStatus(str, Enum):
    PENDING = "pending"
    AVAILABLE = "available"
    VOIDED = "voided"
    REVERSED = "reversed"
    REVIEW_REQUIRED = "review_required"


class ReferralFraudStatus(str, Enum):
    CLEAR = "clear"
    FLAGGED = "flagged"
    REVIEW_REQUIRED = "review_required"


class PartnerLedgerEntryType(str, Enum):
    COMMISSION = "commission"
    REVERSAL = "reversal"
    PAYOUT = "payout"
    ADJUSTMENT = "adjustment"


class PartnerLedgerStatus(str, Enum):
    PENDING = "pending"
    AVAILABLE = "available"
    RESERVED = "reserved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    VOIDED = "voided"


class PartnerPayoutStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    PROCESSING = "processing"
    PAID = "paid"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


def referral_money(value: Decimal | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def commission_from_payment_amount(
    *,
    eligible_amount: Decimal | int,
    rate: Decimal,
) -> Decimal:
    return referral_money(Decimal(str(eligible_amount)) * rate)
