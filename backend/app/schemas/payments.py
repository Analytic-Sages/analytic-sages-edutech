from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.payments import EnrollmentStatus, PaymentProviderName, PaymentStatus


class CheckoutRequest(BaseModel):
    """Exactly one of course_id (self-paced) or cohort_id (instructor-led)."""

    course_id: UUID | None = None
    cohort_id: UUID | None = None
    provider: PaymentProviderName = Field(
        description="paystack | nowpayments (mock checkout until live keys are set)"
    )

    @model_validator(mode="after")
    def require_one_target(self) -> CheckoutRequest:
        if bool(self.course_id) == bool(self.cohort_id):
            raise ValueError("Provide exactly one of course_id or cohort_id")
        if self.provider not in {
            PaymentProviderName.PAYSTACK,
            PaymentProviderName.NOWPAYMENTS,
        }:
            raise ValueError("provider must be paystack or nowpayments")
        return self


class CheckoutResponse(BaseModel):
    order_id: str
    provider: PaymentProviderName
    checkout_url: str
    amount: int
    currency: str
    status: PaymentStatus
    crypto_currency: str | None = None
    crypto_amount: str | None = None
    mode: str
    cohort_id: UUID | None = None
    course_id: UUID | None = None


class PaymentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: str
    course_id: UUID | None
    cohort_id: UUID | None
    provider: PaymentProviderName
    amount: int
    currency: str
    status: PaymentStatus
    crypto_currency: str | None
    crypto_amount: str | None
    confirmed_at: datetime | None
    created_at: datetime


class EnrollmentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    status: EnrollmentStatus
    enrolled_at: datetime
    payment_id: UUID | None


class CoursePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: str
    description: str
    thumbnail: str | None
    category: str
    difficulty: str
    duration: str
    lessons_count: int
    price: int
    currency: str
    published: bool


class MockConfirmRequest(BaseModel):
    order_id: str
    status: PaymentStatus = PaymentStatus.CONFIRMED
    crypto_currency: str | None = None
    crypto_amount: str | None = None


class MessageResponse(BaseModel):
    message: str
