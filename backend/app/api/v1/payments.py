from __future__ import annotations

import hmac
import json
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_payment_service, get_settings
from app.core.config import Settings
from app.core.payments import PaymentProviderName
from app.db.session import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.payments.factory import get_payment_provider
from app.schemas.payments import (
    CheckoutRequest,
    CheckoutResponse,
    CoursePublic,
    EnrollmentPublic,
    MessageResponse,
    MockConfirmRequest,
    PaymentPublic,
)
from app.services.payments import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["payments"])


@router.get("/courses", response_model=list[CoursePublic])
def list_published_courses(db: Session = Depends(get_db)) -> list[Course]:
    return list(
        db.scalars(select(Course).where(Course.published.is_(True)).order_by(Course.title)).all()
    )


@router.get("/courses/{course_id}", response_model=CoursePublic)
def get_course(course_id: UUID, db: Session = Depends(get_db)) -> Course:
    course = db.get(Course, course_id)
    if not course or not course.published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(
    payload: CheckoutRequest,
    current_user: CurrentUser,
    payment_service: PaymentService = Depends(get_payment_service),
) -> CheckoutResponse:
    return payment_service.create_checkout(
        user=current_user,
        course_id=payload.course_id,
        cohort_id=payload.cohort_id,
        provider_name=payload.provider,
        tuition_plan_id=payload.tuition_plan_id,
    )


@router.get("/payments/{order_id}", response_model=PaymentPublic)
def get_payment(
    order_id: str,
    current_user: CurrentUser,
    payment_service: PaymentService = Depends(get_payment_service),
) -> PaymentPublic:
    payment = payment_service.get_payment_for_user(user=current_user, order_id=order_id)
    return PaymentPublic.model_validate(payment)


@router.get("/me/enrollments", response_model=list[EnrollmentPublic])
def my_enrollments(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> list[Enrollment]:
    return list(
        db.scalars(
            select(Enrollment).where(
                Enrollment.user_id == current_user.id,
            )
        ).all()
    )


@router.post("/webhooks/payments/{provider}", response_model=MessageResponse)
async def payment_webhook(
    provider: PaymentProviderName,
    request: Request,
    payment_service: PaymentService = Depends(get_payment_service),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    body = await request.body()
    try:
        payload: dict[str, Any] = json.loads(body.decode() or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        ) from exc

    headers = {k.lower(): v for k, v in request.headers.items()}
    adapter = get_payment_provider(provider, settings)
    try:
        event = adapter.verify_webhook(headers=headers, body=body, payload=payload)
    except HTTPException as exc:
        logger.warning(
            "Payment webhook rejected provider=%s status=%s detail=%s",
            provider.value,
            exc.status_code,
            exc.detail,
        )
        raise
    payment_service.process_webhook_event(event)
    logger.info(
        "Payment webhook processed provider=%s order=%s status=%s",
        provider.value,
        event.order_id,
        event.status.value,
    )
    return MessageResponse(message="Webhook processed")


@router.post("/webhooks/payments/mock/confirm", response_model=MessageResponse)
def mock_confirm_payment(
    payload: MockConfirmRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Dev-only helper used by the mock checkout page to unlock a course."""
    if settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mock confirm is disabled in production",
        )

    from app.models.payment import Payment
    from app.payments.base import WebhookEvent

    payment = db.scalar(select(Payment).where(Payment.order_id == payload.order_id))
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    event = WebhookEvent(
        provider=payment.provider,
        order_id=payment.order_id,
        provider_payment_id=payment.provider_payment_id or f"mock_{payment.order_id}",
        status=payload.status,
        crypto_currency=payload.crypto_currency,
        crypto_amount=payload.crypto_amount,
        raw=payload.model_dump(mode="json"),
    )
    payment_service.process_webhook_event(event)
    return MessageResponse(message=f"Payment {payload.status.value}")


@router.post("/internal/payments/reconcile")
def internal_reconcile_payments(
    payment_service: PaymentService = Depends(get_payment_service),
    settings: Settings = Depends(get_settings),
    x_payments_reconcile_token: str | None = Header(default=None),
    older_than_seconds: int = 120,
    limit: int = 50,
) -> dict[str, int]:
    """Cron/ops hook: pull the real status for stale pending NOWPayments orders.

    Token-protected (PAYMENTS_RECONCILE_TOKEN, falling back to
    OPPORTUNITY_SYNC_TOKEN). Complements the in-process background sweep for
    deployments that would rather drive reconciliation from a scheduler.
    """
    expected = (settings.payments_reconcile_token or settings.opportunity_sync_token or "").strip()
    if not expected:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    provided = (x_payments_reconcile_token or "").strip()
    if len(provided) != len(expected) or not hmac.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reconcile token"
        )
    return payment_service.reconcile_stale_nowpayments(
        older_than_seconds=max(older_than_seconds, 0),
        limit=max(1, min(limit, 200)),
    )
