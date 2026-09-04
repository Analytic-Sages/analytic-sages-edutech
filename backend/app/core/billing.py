from __future__ import annotations

import enum


class TuitionPlanType(str, enum.Enum):
    ONE_TIME = "one_time"
    INSTALLMENT = "installment"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class DueRule(str, enum.Enum):
    IMMEDIATE = "immediate"
    SPECIFIC_DATE = "specific_date"
    WEEK_NUMBER = "week_number"
    BEFORE_COHORT_START = "before_cohort_start"


class BillingStatus(str, enum.Enum):
    PENDING = "pending"
    CURRENT = "current"
    PAST_DUE = "past_due"
    GRACE_PERIOD = "grace_period"
    PAYMENT_HOLD = "payment_hold"
    PAID_IN_FULL = "paid_in_full"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class ObligationStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    OPEN = "open"
    PROCESSING = "processing"
    PAID = "paid"
    PAST_DUE = "past_due"
    WAIVED = "waived"
    CANCELLED = "cancelled"
