from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.billing import BillingStatus, DueRule, ObligationStatus, TuitionPlanType
from app.core.config import get_settings
from app.core.payments import PaymentProviderName, PaymentStatus
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.billing import PaymentObligation, StudentBillingAccount, TuitionPlan
from app.models.classroom import Cohort, CohortMember, CohortStatus
from app.models.payment import Payment
from app.models.user import User
from app.payments.base import WebhookEvent
from app.schemas.billing import TuitionPlanCreate, TuitionPlanScheduleCreate
from app.services.billing_accounts import BillingAccountService
from app.services.billing_obligations import PaymentObligationService
from app.services.billing_reconciliation import BillingReconciliationService
from app.services.email import EmailService
from app.services.payments import PaymentService
from app.services.tuition_plans import TuitionPlanService, money

client = TestClient(app)

COHORT_SLUG = "test-billing-cohort"


def _token_for(user: User) -> str:
    return SecurityService(get_settings()).create_access_token(
        user_id=str(user.id), role=user.role.value
    )


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_for(user)}"}


def _make_user(email: str, role: UserRole = UserRole.STUDENT) -> User:
    db = SessionLocal()
    try:
        user = User(
            email=email,
            full_name="Billing Test",
            role=role,
            email_verified=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def _cleanup() -> None:
    db = SessionLocal()
    try:
        cohort = db.scalar(select(Cohort).where(Cohort.slug == COHORT_SLUG))
        if cohort:
            accounts = list(
                db.scalars(
                    select(StudentBillingAccount).where(
                        StudentBillingAccount.cohort_id == cohort.id
                    )
                ).all()
            )
            for account in accounts:
                for payment in db.scalars(
                    select(Payment).where(Payment.billing_account_id == account.id)
                ).all():
                    db.delete(payment)
                db.delete(account)
            for plan in db.scalars(
                select(TuitionPlan).where(TuitionPlan.cohort_id == cohort.id)
            ).all():
                db.delete(plan)
            for member in db.scalars(
                select(CohortMember).where(CohortMember.cohort_id == cohort.id)
            ).all():
                db.delete(member)
            for payment in db.scalars(
                select(Payment).where(Payment.cohort_id == cohort.id)
            ).all():
                db.delete(payment)
            db.delete(cohort)
        for user in db.scalars(
            select(User).where(User.email.like("billing-test-%@example.com"))
        ).all():
            db.delete(user)
        db.commit()
    finally:
        db.close()


def _seed_cohort() -> Cohort:
    db = SessionLocal()
    try:
        existing = db.scalar(select(Cohort).where(Cohort.slug == COHORT_SLUG))
        if existing:
            return existing
        cohort = Cohort(
            id=uuid.uuid4(),
            name="Billing Test Cohort",
            slug=COHORT_SLUG,
            description="Tuition billing tests",
            status=CohortStatus.OPEN,
            registration_deadline=datetime.now(UTC) + timedelta(days=30),
            starts_at=datetime.now(UTC) + timedelta(days=7),
            ends_at=datetime.now(UTC) + timedelta(days=35),
            price=200,
            currency="USD",
        )
        db.add(cohort)
        db.commit()
        db.refresh(cohort)
        return cohort
    finally:
        db.close()


@pytest.fixture
def billing_env(monkeypatch):
    _cleanup()
    cohort = _seed_cohort()
    monkeypatch.setattr(get_settings(), "billing_plans_enabled", True)
    yield cohort
    _cleanup()


def test_plan_schedule_must_sum_to_base(billing_env):
    db = SessionLocal()
    try:
        service = TuitionPlanService(db)
        with pytest.raises(Exception):
            service.create_plan(
                TuitionPlanCreate(
                    cohort_id=billing_env.id,
                    name="Bad plan",
                    plan_type=TuitionPlanType.INSTALLMENT,
                    base_amount=Decimal("200.00"),
                    schedules=[
                        TuitionPlanScheduleCreate(
                            sequence_number=1, amount=Decimal("100.00")
                        ),
                        TuitionPlanScheduleCreate(
                            sequence_number=2, amount=Decimal("50.00")
                        ),
                    ],
                )
            )
    finally:
        db.close()


def test_obligation_generation_and_first_open(billing_env):
    db = SessionLocal()
    try:
        student = _make_user(f"billing-test-{uuid.uuid4().hex[:8]}@example.com")
        plans = TuitionPlanService(db)
        plan = plans.create_plan(
            TuitionPlanCreate(
                cohort_id=billing_env.id,
                name="Pay in 2",
                plan_type=TuitionPlanType.INSTALLMENT,
                base_amount=Decimal("220.00"),
                schedules=[
                    TuitionPlanScheduleCreate(
                        sequence_number=1,
                        label="Installment 1",
                        amount=Decimal("110.00"),
                        due_rule=DueRule.IMMEDIATE,
                    ),
                    TuitionPlanScheduleCreate(
                        sequence_number=2,
                        label="Installment 2",
                        amount=Decimal("110.00"),
                        due_rule=DueRule.SPECIFIC_DATE,
                        due_date=datetime.now(UTC) + timedelta(days=21),
                    ),
                ],
            )
        )
        account = BillingAccountService(db).create_account(
            student=student,
            tuition_plan_id=plan.id,
            cohort_id=billing_env.id,
        )
        assert len(account.obligations) == 2
        assert account.obligations[0].status == ObligationStatus.OPEN
        assert account.obligations[1].status == ObligationStatus.UPCOMING
        assert money(account.final_amount_due) == Decimal("220.00")
    finally:
        db.close()


def test_checkout_requires_plan_when_enabled(billing_env):
    db = SessionLocal()
    try:
        student = _make_user(f"billing-test-{uuid.uuid4().hex[:8]}@example.com")
        TuitionPlanService(db).create_plan(
            TuitionPlanCreate(
                cohort_id=billing_env.id,
                name="Pay in Full",
                plan_type=TuitionPlanType.ONE_TIME,
                base_amount=Decimal("200.00"),
                schedules=[
                    TuitionPlanScheduleCreate(
                        sequence_number=1, amount=Decimal("200.00")
                    )
                ],
            )
        )
        response = client.post(
            "/api/v1/checkout",
            headers=_auth(student),
            json={
                "cohort_id": str(billing_env.id),
                "provider": "paystack",
            },
        )
        assert response.status_code == 400
        assert "tuition plan" in response.json()["detail"].lower()
    finally:
        db.close()


def test_reconcile_first_payment_unlocks_and_duplicate_webhook_safe(billing_env):
    db = SessionLocal()
    try:
        student = _make_user(f"billing-test-{uuid.uuid4().hex[:8]}@example.com")
        plan = TuitionPlanService(db).create_plan(
            TuitionPlanCreate(
                cohort_id=billing_env.id,
                name="Installments",
                plan_type=TuitionPlanType.INSTALLMENT,
                base_amount=Decimal("220.00"),
                schedules=[
                    TuitionPlanScheduleCreate(
                        sequence_number=1, amount=Decimal("110.00")
                    ),
                    TuitionPlanScheduleCreate(
                        sequence_number=2,
                        amount=Decimal("110.00"),
                        due_rule=DueRule.SPECIFIC_DATE,
                        due_date=datetime.now(UTC) + timedelta(days=14),
                    ),
                ],
            )
        )
        checkout = client.post(
            "/api/v1/checkout",
            headers=_auth(student),
            json={
                "cohort_id": str(billing_env.id),
                "provider": "paystack",
                "tuition_plan_id": str(plan.id),
            },
        )
        assert checkout.status_code == 200, checkout.text
        order_id = checkout.json()["order_id"]
        assert checkout.json()["amount"] == 110

        settings = get_settings()
        payment_service = PaymentService(db, settings, EmailService(settings))
        event = WebhookEvent(
            provider=PaymentProviderName.PAYSTACK,
            order_id=order_id,
            provider_payment_id=f"psk_{order_id}",
            status=PaymentStatus.CONFIRMED,
            raw={"verified": {"amount": 110 * 100, "currency": "USD"}},
        )
        # Bypass Paystack FX metadata by using mock provider path in non-prod:
        payment = db.scalar(select(Payment).where(Payment.order_id == order_id))
        assert payment is not None
        payment.provider = PaymentProviderName.MOCK
        db.commit()

        event = WebhookEvent(
            provider=PaymentProviderName.MOCK,
            order_id=order_id,
            provider_payment_id=f"mock_{order_id}",
            status=PaymentStatus.CONFIRMED,
            raw={"mock": True},
        )
        payment_service.process_webhook_event(event)
        payment_service.process_webhook_event(event)

        account = db.scalar(
            select(StudentBillingAccount)
            .options(selectinload(StudentBillingAccount.obligations))
            .where(StudentBillingAccount.student_id == student.id)
        )
        assert account is not None
        assert account.obligations[0].status == ObligationStatus.PAID
        assert account.obligations[1].status == ObligationStatus.OPEN
        assert account.billing_status == BillingStatus.CURRENT
        assert money(account.amount_paid) == Decimal("110.00")
        assert money(account.amount_outstanding) == Decimal("110.00")

        member = db.scalar(
            select(CohortMember).where(
                CohortMember.cohort_id == billing_env.id,
                CohortMember.user_id == student.id,
            )
        )
        assert member is not None
    finally:
        db.close()


def test_failed_attempt_reopens_obligation(billing_env):
    db = SessionLocal()
    try:
        student = _make_user(f"billing-test-{uuid.uuid4().hex[:8]}@example.com")
        plan = TuitionPlanService(db).create_plan(
            TuitionPlanCreate(
                cohort_id=billing_env.id,
                name="Full",
                plan_type=TuitionPlanType.ONE_TIME,
                base_amount=Decimal("200.00"),
                schedules=[
                    TuitionPlanScheduleCreate(
                        sequence_number=1, amount=Decimal("200.00")
                    )
                ],
            )
        )
        checkout = client.post(
            "/api/v1/checkout",
            headers=_auth(student),
            json={
                "cohort_id": str(billing_env.id),
                "provider": "paystack",
                "tuition_plan_id": str(plan.id),
            },
        )
        assert checkout.status_code == 200
        order_id = checkout.json()["order_id"]
        payment = db.scalar(select(Payment).where(Payment.order_id == order_id))
        assert payment is not None
        payment.provider = PaymentProviderName.MOCK
        db.commit()

        settings = get_settings()
        PaymentService(db, settings, EmailService(settings)).process_webhook_event(
            WebhookEvent(
                provider=PaymentProviderName.MOCK,
                order_id=order_id,
                provider_payment_id=f"fail_{order_id}",
                status=PaymentStatus.FAILED,
                raw={},
            )
        )
        obligation = db.get(PaymentObligation, payment.payment_obligation_id)
        assert obligation is not None
        assert obligation.status == ObligationStatus.OPEN
    finally:
        db.close()


def test_waive_and_unauthorized_account(billing_env):
    db = SessionLocal()
    try:
        student = _make_user(f"billing-test-{uuid.uuid4().hex[:8]}@example.com")
        other = _make_user(f"billing-test-{uuid.uuid4().hex[:8]}@example.com")
        admin = _make_user(
            f"billing-test-admin-{uuid.uuid4().hex[:8]}@example.com",
            role=UserRole.ADMIN,
        )
        plan = TuitionPlanService(db).create_plan(
            TuitionPlanCreate(
                cohort_id=billing_env.id,
                name="Two",
                plan_type=TuitionPlanType.INSTALLMENT,
                base_amount=Decimal("220.00"),
                schedules=[
                    TuitionPlanScheduleCreate(
                        sequence_number=1, amount=Decimal("110.00")
                    ),
                    TuitionPlanScheduleCreate(
                        sequence_number=2,
                        amount=Decimal("110.00"),
                        due_rule=DueRule.SPECIFIC_DATE,
                        due_date=datetime.now(UTC) + timedelta(days=10),
                    ),
                ],
            )
        )
        account = BillingAccountService(db).create_account(
            student=student, tuition_plan_id=plan.id, cohort_id=billing_env.id
        )
        forbidden = client.get(
            f"/api/v1/billing/me/accounts/{account.id}",
            headers=_auth(other),
        )
        assert forbidden.status_code == 404

        second = account.obligations[1]
        waived = client.post(
            f"/api/v1/admin/billing/obligations/{second.id}/waive",
            headers=_auth(admin),
            json={"note": "scholarship"},
        )
        assert waived.status_code == 200
        assert waived.json()["obligations"][1]["status"] == "waived"
    finally:
        db.close()


def test_legacy_checkout_when_flag_off(billing_env, monkeypatch):
    monkeypatch.setattr(get_settings(), "billing_plans_enabled", False)
    student = _make_user(f"billing-test-{uuid.uuid4().hex[:8]}@example.com")
    response = client.post(
        "/api/v1/checkout",
        headers=_auth(student),
        json={"cohort_id": str(billing_env.id), "provider": "paystack"},
    )
    assert response.status_code == 200
    assert response.json()["amount"] == 200
