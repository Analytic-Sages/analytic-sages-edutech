from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.billing import DueRule, ObligationStatus, TuitionPlanType
from app.core.config import get_settings
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.billing import PaymentObligation, StudentBillingAccount, TuitionPlan
from app.models.classroom import Cohort, CohortMember, CohortStatus
from app.models.user import User
from app.schemas.billing import TuitionPlanCreate, TuitionPlanScheduleCreate
from app.services.billing_accounts import BillingAccountService
from app.services.billing_reminders import BillingReminderService
from app.services.email import EmailService
from app.services.tuition_plans import TuitionPlanService

client = TestClient(app)

COHORT_SLUG = "billing-reminders-test-cohort"


def _token_for(user: User) -> str:
    return SecurityService(get_settings()).create_access_token(
        user_id=str(user.id), role=user.role.value
    )


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_for(user)}"}


def _make_user(prefix: str, role: UserRole = UserRole.STUDENT) -> User:
    db = SessionLocal()
    try:
        user = User(
            email=f"{prefix}-{uuid.uuid4().hex[:8]}@example.com",
            full_name="Reminder Test",
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
            for account in db.scalars(
                select(StudentBillingAccount).where(
                    StudentBillingAccount.cohort_id == cohort.id
                )
            ).all():
                db.delete(account)
            for plan in db.scalars(
                select(TuitionPlan).where(TuitionPlan.cohort_id == cohort.id)
            ).all():
                db.delete(plan)
            for member in db.scalars(
                select(CohortMember).where(CohortMember.cohort_id == cohort.id)
            ).all():
                db.delete(member)
            db.delete(cohort)
        for user in db.scalars(
            select(User).where(User.email.like("billing-reminders-%@example.com"))
        ).all():
            db.delete(user)
        db.commit()
    finally:
        db.close()


def _seed_cohort() -> Cohort:
    db = SessionLocal()
    try:
        cohort = Cohort(
            id=uuid.uuid4(),
            name="Billing Reminders Test Cohort",
            slug=COHORT_SLUG,
            description="reminders tests",
            status=CohortStatus.OPEN,
            registration_deadline=datetime.now(UTC) + timedelta(days=30),
            starts_at=datetime.now(UTC) + timedelta(days=7),
            ends_at=datetime.now(UTC) + timedelta(days=60),
            price=200,
            currency="USD",
        )
        db.add(cohort)
        db.commit()
        db.refresh(cohort)
        return cohort
    finally:
        db.close()


def _account_with_overdue(cohort: Cohort, state: str = "overdue") -> dict:
    db = SessionLocal()
    try:
        student = _make_user("billing-reminders")
        plan = TuitionPlanService(db).create_plan(
            TuitionPlanCreate(
                cohort_id=cohort.id,
                name=f"Pay in 2 {uuid.uuid4().hex[:4]}",
                plan_type=TuitionPlanType.INSTALLMENT,
                base_amount=Decimal("200.00"),
                schedules=[
                    TuitionPlanScheduleCreate(
                        sequence_number=1,
                        label="Installment 1",
                        amount=Decimal("100.00"),
                        due_rule=DueRule.IMMEDIATE,
                    ),
                    TuitionPlanScheduleCreate(
                        sequence_number=2,
                        label="Installment 2",
                        amount=Decimal("100.00"),
                        due_rule=DueRule.SPECIFIC_DATE,
                        due_date=datetime.now(UTC) + timedelta(days=21),
                    ),
                ],
            )
        )
        account = BillingAccountService(db).create_account(
            student=student, tuition_plan_id=plan.id, cohort_id=cohort.id
        )
        obligations = sorted(account.obligations, key=lambda o: o.sequence_number)
        now = datetime.now(UTC)
        if state == "overdue":
            obligations[0].due_date = now - timedelta(days=1)
            obligations[0].status = ObligationStatus.OPEN
        elif state == "due_soon":
            obligations[0].due_date = now + timedelta(days=2)
            obligations[0].status = ObligationStatus.OPEN
        elif state == "future":
            obligations[0].due_date = now + timedelta(days=40)
            obligations[0].status = ObligationStatus.OPEN
        db.commit()
        return {
            "account_id": account.id,
            "student_id": student.id,
            "obligation_ids": [obligation.id for obligation in obligations],
        }
    finally:
        db.close()


@pytest.fixture
def reminders_env():
    _cleanup()
    cohort = _seed_cohort()
    yield cohort
    _cleanup()


@pytest.fixture
def sent_emails(monkeypatch):
    calls: list[dict] = []

    def _fake(self, **kwargs):
        calls.append(kwargs)
        return True

    monkeypatch.setattr(EmailService, "send_installment_reminder", _fake)
    return calls


def test_remind_obligation_sends_and_marks(reminders_env, sent_emails):
    setup = _account_with_overdue(reminders_env, "overdue")
    db = SessionLocal()
    try:
        service = BillingReminderService(db, EmailService(get_settings()))
        assert service.remind_obligation(setup["obligation_ids"][0]) is True
        assert len(sent_emails) == 1
        assert sent_emails[0]["kind"] == "overdue"

        refreshed = db.get(PaymentObligation, setup["obligation_ids"][0])
        assert refreshed is not None and refreshed.reminder_sent_at is not None
    finally:
        db.close()


def test_run_overdue_scope_only(reminders_env, sent_emails):
    _account_with_overdue(reminders_env, "overdue")
    future = _account_with_overdue(reminders_env, "future")
    db = SessionLocal()
    try:
        service = BillingReminderService(db, EmailService(get_settings()))
        outcome = service.run(scope="overdue", cohort_id=reminders_env.id)
        assert outcome.sent == 1
        assert len(sent_emails) == 1
        future_obligation = db.get(PaymentObligation, future["obligation_ids"][0])
        assert future_obligation is not None and future_obligation.reminder_sent_at is None
    finally:
        db.close()


def test_run_is_idempotent_for_non_overdue(reminders_env, sent_emails):
    _account_with_overdue(reminders_env, "due_soon")
    db = SessionLocal()
    try:
        service = BillingReminderService(db, EmailService(get_settings()))
        first = service.run(scope="due_soon", cohort_id=reminders_env.id)
        assert first.sent == 1
        second = service.run(scope="due_soon", cohort_id=reminders_env.id)
        assert second.sent == 0
        assert second.skipped >= 1
        assert len(sent_emails) == 1
    finally:
        db.close()


def test_admin_bulk_remind_endpoint(reminders_env, sent_emails):
    _account_with_overdue(reminders_env, "overdue")
    admin = _make_user("billing-reminders", UserRole.ADMIN)
    try:
        response = client.post(
            "/api/v1/admin/installments/remind",
            headers=_auth(admin),
            json={"scope": "overdue", "cohort_id": str(reminders_env.id)},
        )
        assert response.status_code == 200
        assert response.json()["sent"] == 1
    finally:
        _cleanup()


def test_admin_remind_requires_admin(reminders_env, sent_emails):
    student = _make_user("billing-reminders")
    try:
        response = client.post(
            "/api/v1/admin/installments/remind",
            headers=_auth(student),
            json={"scope": "overdue"},
        )
        assert response.status_code == 403
    finally:
        _cleanup()


def test_internal_reminder_endpoint_token(reminders_env, sent_emails, monkeypatch):
    _account_with_overdue(reminders_env, "overdue")
    monkeypatch.setattr(get_settings(), "billing_reminders_token", "secret-reminders")
    # Missing token → 401
    assert (
        client.post(
            "/api/v1/internal/billing/run-reminders", json={"scope": "overdue"}
        ).status_code
        == 401
    )
    # Correct token → 200
    response = client.post(
        "/api/v1/internal/billing/run-reminders",
        json={"scope": "overdue"},
        headers={"X-Billing-Reminders-Token": "secret-reminders"},
    )
    assert response.status_code == 200
    assert response.json()["sent"] == 1


def test_internal_reminder_endpoint_disabled_without_token(reminders_env, monkeypatch):
    monkeypatch.setattr(get_settings(), "billing_reminders_token", None)
    monkeypatch.setattr(get_settings(), "opportunity_sync_token", None)
    response = client.post(
        "/api/v1/internal/billing/run-reminders", json={"scope": "overdue"}
    )
    assert response.status_code == 404