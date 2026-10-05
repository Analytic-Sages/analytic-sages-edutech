from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.core.billing import BillingStatus, DueRule, ObligationStatus, TuitionPlanType
from app.core.payments import PaymentProviderName, PaymentStatus


class TuitionPlanScheduleCreate(BaseModel):
    sequence_number: int = Field(ge=1)
    label: str | None = None
    amount: Decimal
    due_rule: DueRule = DueRule.IMMEDIATE
    due_date: datetime | None = None
    week_number: int | None = Field(default=None, ge=1)
    offset_days: int | None = None


class TuitionPlanSchedulePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sequence_number: int
    label: str | None
    amount: Decimal
    due_rule: DueRule
    due_date: datetime | None
    week_number: int | None
    offset_days: int | None


class TuitionPlanCreate(BaseModel):
    course_id: UUID | None = None
    cohort_id: UUID | None = None
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    plan_type: TuitionPlanType = TuitionPlanType.ONE_TIME
    base_currency: str = Field(default="USD", min_length=3, max_length=3)
    base_amount: Decimal
    active: bool = True
    available_from: datetime | None = None
    available_until: datetime | None = None
    sort_order: int = 0
    schedules: list[TuitionPlanScheduleCreate]

    @field_validator("base_currency")
    @classmethod
    def upper_currency(cls, value: str) -> str:
        return value.upper()


class TuitionPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    plan_type: TuitionPlanType | None = None
    base_currency: str | None = Field(default=None, min_length=3, max_length=3)
    base_amount: Decimal | None = None
    active: bool | None = None
    available_from: datetime | None = None
    available_until: datetime | None = None
    sort_order: int | None = None
    schedules: list[TuitionPlanScheduleCreate] | None = None


class TuitionPlanPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID | None
    cohort_id: UUID | None
    name: str
    description: str | None
    plan_type: TuitionPlanType
    base_currency: str
    base_amount: Decimal
    number_of_installments: int
    active: bool
    sort_order: int
    schedules: list[TuitionPlanSchedulePublic] = []


class CreateBillingAccountRequest(BaseModel):
    tuition_plan_id: UUID
    cohort_id: UUID | None = None
    course_id: UUID | None = None


class ObligationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sequence_number: int
    description: str
    amount_due: Decimal
    currency: str
    due_date: datetime | None
    status: ObligationStatus
    paid_amount: Decimal
    paid_at: datetime | None


class BillingAccountPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    course_id: UUID | None
    cohort_id: UUID | None
    tuition_plan_id: UUID
    currency: str
    total_amount: Decimal
    discount_amount: Decimal
    scholarship_amount: Decimal
    final_amount_due: Decimal
    amount_paid: Decimal
    amount_outstanding: Decimal
    billing_status: BillingStatus
    access_blocked: bool = False
    created_at: datetime
    obligations: list[ObligationPublic] = []
    tuition_plan: TuitionPlanPublic | None = None

    def _next_open_obligation(self) -> ObligationPublic | None:
        pending = [
            o
            for o in self.obligations
            if o.status
            not in {
                ObligationStatus.PAID,
                ObligationStatus.WAIVED,
                ObligationStatus.CANCELLED,
            }
        ]
        pending.sort(key=lambda o: o.sequence_number)
        return pending[0] if pending else None

    @computed_field
    @property
    def plan_name(self) -> str | None:
        """Tuition plan the student is on (e.g. 'Pay in Full', 'Pay in 2')."""
        return self.tuition_plan.name if self.tuition_plan else None

    @computed_field
    @property
    def plan_type(self) -> TuitionPlanType | None:
        return self.tuition_plan.plan_type if self.tuition_plan else None

    @computed_field
    @property
    def installments_total(self) -> int:
        if self.obligations:
            return len(self.obligations)
        return self.tuition_plan.number_of_installments if self.tuition_plan else 0

    @computed_field
    @property
    def installments_paid(self) -> int:
        return sum(
            1
            for o in self.obligations
            if o.status in {ObligationStatus.PAID, ObligationStatus.WAIVED}
        )

    @computed_field
    @property
    def installments_remaining(self) -> int:
        return max(0, self.installments_total - self.installments_paid)

    @computed_field
    @property
    def is_paid_in_full(self) -> bool:
        """True once nothing is owed — includes a fully-paid installment plan."""
        if self.billing_status == BillingStatus.PAID_IN_FULL:
            return True
        return self.amount_outstanding <= Decimal("0.00")

    @computed_field
    @property
    def next_due_date(self) -> datetime | None:
        """Due date of the next unpaid installment (None when paid in full)."""
        nxt = self._next_open_obligation()
        return nxt.due_date if nxt else None

    @computed_field
    @property
    def next_due_amount(self) -> Decimal | None:
        nxt = self._next_open_obligation()
        return nxt.amount_due if nxt else None

    @computed_field
    @property
    def next_due_status(self) -> ObligationStatus | None:
        nxt = self._next_open_obligation()
        return nxt.status if nxt else None


class PayObligationRequest(BaseModel):
    provider: PaymentProviderName

    @field_validator("provider")
    @classmethod
    def provider_allowed(cls, value: PaymentProviderName) -> PaymentProviderName:
        if value not in {PaymentProviderName.PAYSTACK, PaymentProviderName.NOWPAYMENTS}:
            raise ValueError("provider must be paystack or nowpayments")
        return value


class AdminBillingAccountPatch(BaseModel):
    billing_status: BillingStatus
    note: str | None = None


class AdminWaiveRequest(BaseModel):
    note: str | None = None


class AdminExtendRequest(BaseModel):
    due_date: datetime
    note: str | None = None


class AdminExtendNextDueRequest(BaseModel):
    due_date: datetime
    note: str | None = None


class AdminAccountAccessRequest(BaseModel):
    access_blocked: bool
    note: str | None = None


class AdminManualPaymentRequest(BaseModel):
    amount: Decimal
    note: str | None = None
    unlock_access: bool = True


class BillingPaymentAttemptPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: str
    provider: PaymentProviderName
    amount: int
    currency: str
    status: PaymentStatus
    payment_obligation_id: UUID | None
    confirmed_at: datetime | None
    created_at: datetime
