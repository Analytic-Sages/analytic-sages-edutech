from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
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


def _two_plans(db, cohort_id) -> tuple[TuitionPlan, TuitionPlan]:
    """A Pay-in-Full plan and a 2-installment plan, mirroring BDE seeding."""
    plans = TuitionPlanService(db)
    full = plans.create_plan(
        TuitionPlanCreate(
            cohort_id=cohort_id,
            name="Pay in Full",
            plan_type=TuitionPlanType.ONE_TIME,
            base_amount=Decimal("200.00"),
            schedules=[
                TuitionPlanScheduleCreate(sequence_number=1, amount=Decimal("200.00"))
            ],
        )
    )
    installments = plans.create_plan(
        TuitionPlanCreate(
            cohort_id=cohort_id,
            name="Pay in 2 Installments",
            plan_type=TuitionPlanType.INSTALLMENT,
            base_amount=Decimal("220.00"),
            schedules=[
                TuitionPlanScheduleCreate(
                    sequence_number=1,
                    amount=Decimal("110.00"),
                    due_rule=DueRule.IMMEDIATE,
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
    return full, installments


def test_student_can_switch_plan_before_payment(billing_env):
    db = SessionLocal()
    try:
        student = _make_user(f"billing-test-{uuid.uuid4().hex[:8]}@example.com")
        full, installments = _two_plans(db, billing_env.id)
        accounts = BillingAccountService(db)

        account = accounts.create_account(
            student=student, tuition_plan_id=full.id, cohort_id=billing_env.id
        )
        assert account.tuition_plan_id == full.id
        assert len(account.obligations) == 1

        # Student changes their mind before paying a cent.
        switched = accounts.create_account(
            student=student, tuition_plan_id=installments.id, cohort_id=billing_env.id
        )
        assert switched.id == account.id  # same enrollment, no duplicate account
        assert switched.tuition_plan_id == installments.id
        assert [o.sequence_number for o in switched.obligations] == [1, 2]
        assert switched.obligations[0].status == ObligationStatus.OPEN
        assert switched.obligations[1].status == ObligationStatus.UPCOMING
        assert money(switched.total_amount) == Decimal("220.00")
        assert money(switched.final_amount_due) == Decimal("220.00")
        assert money(switched.amount_outstanding) == Decimal("220.00")
        assert switched.billing_status == BillingStatus.PENDING
    finally:
        db.close()


def test_abandoned_full_checkout_can_switch_to_installments(billing_env):
    """The reported bug: full-payment checkout abandoned, then installments chosen."""
    db = SessionLocal()
    try:
        student = _make_user(f"billing-test-{uuid.uuid4().hex[:8]}@example.com")
        full, installments = _two_plans(db, billing_env.id)

        first = client.post(
            "/api/v1/checkout",
            headers=_auth(student),
            json={
                "cohort_id": str(billing_env.id),
                "provider": "paystack",
                "tuition_plan_id": str(full.id),
            },
        )
        assert first.status_code == 200, first.text
        assert first.json()["amount"] == 200

        second = client.post(
            "/api/v1/checkout",
            headers=_auth(student),
            json={
                "cohort_id": str(billing_env.id),
                "provider": "paystack",
                "tuition_plan_id": str(installments.id),
            },
        )
        assert second.status_code == 200, second.text
        assert second.json()["amount"] == 110

        account = db.scalar(
            select(StudentBillingAccount)
            .options(selectinload(StudentBillingAccount.obligations))
            .where(StudentBillingAccount.student_id == student.id)
        )
        assert account is not None
        assert account.tuition_plan_id == installments.id
        assert len(account.obligations) == 2
        assert money(account.final_amount_due) == Decimal("220.00")

        # The abandoned full-payment checkout is expired so it can't be confirmed.
        abandoned = db.scalar(
            select(Payment).where(Payment.order_id == first.json()["order_id"])
        )
        assert abandoned is not None
        assert abandoned.status == PaymentStatus.EXPIRED
    finally:
        db.close()


def test_plan_switch_blocked_after_payment(billing_env):
    db = SessionLocal()
    try:
        student = _make_user(f"billing-test-{uuid.uuid4().hex[:8]}@example.com")
        full, installments = _two_plans(db, billing_env.id)
        accounts = BillingAccountService(db)

        account = accounts.create_account(
            student=student, tuition_plan_id=full.id, cohort_id=billing_env.id
        )
        db.add(
            Payment(
                order_id=f"switch-{uuid.uuid4().hex[:12]}",
                user_id=student.id,
                cohort_id=billing_env.id,
                billing_account_id=account.id,
                payment_obligation_id=account.obligations[0].id,
                provider=PaymentProviderName.MOCK,
                provider_payment_id=f"mock_{uuid.uuid4().hex[:8]}",
                amount=200,
                currency="USD",
                status=PaymentStatus.CONFIRMED,
                confirmed_at=datetime.now(UTC),
            )
        )
        db.commit()

        with pytest.raises(HTTPException) as excinfo:
            accounts.create_account(
                student=student, tuition_plan_id=installments.id, cohort_id=billing_env.id
            )
        assert excinfo.value.status_code == 409
    finally:
        db.close()


def test_billing_account_public_exposes_plan_progress_and_next_due():
    """Admin board derives paid-in-full vs installment and the next deadline here."""
    from app.schemas.billing import (
        BillingAccountPublic,
        ObligationPublic,
        TuitionPlanPublic,
    )

    now = datetime.now(UTC)
    plan = TuitionPlanPublic(
        id=uuid.uuid4(),
        course_id=None,
        cohort_id=uuid.uuid4(),
        name="Pay in 2 Installments",
        description=None,
        plan_type=TuitionPlanType.INSTALLMENT,
        base_currency="USD",
        base_amount=Decimal("220.00"),
        number_of_installments=2,
        active=True,
        sort_order=0,
        schedules=[],
    )
    obligations = [
        ObligationPublic(
            id=uuid.uuid4(),
            sequence_number=1,
            description="Installment 1",
            amount_due=Decimal("110.00"),
            currency="USD",
            due_date=now,
            status=ObligationStatus.PAID,
            paid_amount=Decimal("110.00"),
            paid_at=now,
        ),
        ObligationPublic(
            id=uuid.uuid4(),
            sequence_number=2,
            description="Installment 2",
            amount_due=Decimal("110.00"),
            currency="USD",
            due_date=now + timedelta(days=14),
            status=ObligationStatus.OPEN,
            paid_amount=Decimal("0.00"),
            paid_at=None,
        ),
    ]
    account = BillingAccountPublic(
        id=uuid.uuid4(),
        student_id=uuid.uuid4(),
        course_id=None,
        cohort_id=plan.cohort_id,
        tuition_plan_id=plan.id,
        currency="USD",
        total_amount=Decimal("220.00"),
        discount_amount=Decimal("0.00"),
        scholarship_amount=Decimal("0.00"),
        final_amount_due=Decimal("220.00"),
        amount_paid=Decimal("110.00"),
        amount_outstanding=Decimal("110.00"),
        billing_status=BillingStatus.CURRENT,
        created_at=now,
        obligations=obligations,
        tuition_plan=plan,
    )
    assert account.plan_name == "Pay in 2 Installments"
    assert account.plan_type == TuitionPlanType.INSTALLMENT
    assert account.installments_total == 2
    assert account.installments_paid == 1
    assert account.installments_remaining == 1
    assert account.is_paid_in_full is False
    assert account.next_due_status == ObligationStatus.OPEN
    assert money(account.next_due_amount) == Decimal("110.00")

    # Serialized (what the API returns to the admin board) includes the computed keys.
    dumped = account.model_dump(mode="json")
    assert dumped["installments_paid"] == 1
    assert dumped["plan_name"] == "Pay in 2 Installments"
    assert dumped["next_due_date"] is not None

