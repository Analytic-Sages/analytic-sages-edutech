from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class AdminStudentRow(BaseModel):
    """One row in the admin students view (paid vs unpaid at a glance)."""

    user_id: UUID
    email: EmailStr
    full_name: str | None
    role: str
    cohorts: list[str] = Field(default_factory=list)
    courses: list[str] = Field(default_factory=list)
    plan_name: str | None = None
    plan_type: str | None = None
    payment_status: str  # paid | partial | unpaid
    currency: str | None = None
    amount_paid: Decimal = Decimal("0.00")
    amount_outstanding: Decimal = Decimal("0.00")
    installments_total: int = 0
    installments_paid: int = 0
    next_due_date: datetime | None = None
    next_due_amount: Decimal | None = None
    next_due_status: str | None = None
    has_outstanding: bool = False
    billing_account_id: UUID | None = None
    created_at: datetime


class AdminStudentList(BaseModel):
    rows: list[AdminStudentRow]
    total: int
    paid: int
    partial: int
    unpaid: int


class AdminInstallmentRow(BaseModel):
    obligation_id: UUID
    billing_account_id: UUID
    user_id: UUID
    email: EmailStr
    full_name: str | None
    cohort_name: str | None
    course_title: str | None
    plan_name: str | None
    sequence_number: int
    installments_total: int
    description: str
    amount_due: Decimal
    currency: str
    due_date: datetime | None
    status: str  # upcoming | open | processing | past_due | paid | waived | cancelled
    bucket: str  # overdue | due_soon | upcoming | paid
    days_until_due: int | None
    reminder_sent_at: datetime | None


class InstallmentReminderRequest(BaseModel):
    scope: str = Field(default="overdue", pattern="^(overdue|due_soon|all)$")
    cohort_id: UUID | None = None


class ReminderResult(BaseModel):
    sent: int
    skipped: int
    failed: int