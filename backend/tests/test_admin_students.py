from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.billing import BillingStatus, DueRule, ObligationStatus, TuitionPlanType
from app.core.config import get_settings
from app.core.payments import PaymentProviderName, PaymentStatus
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.billing import StudentBillingAccount, TuitionPlan
from app.models.classroom import Cohort, CohortMember, CohortMemberRole, CohortStatus
from app.models.payment import Payment
from app.models.user import User
from app.schemas.billing import TuitionPlanCreate, TuitionPlanScheduleCreate
from app.services.admin_students import AdminStudentsService
from app.services.billing_accounts import BillingAccountService
from app.services.tuition_plans import TuitionPlanService, money

client = TestClient(app)

COHORT_SLUG = "admin-students-test-cohort"


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
            full_name="Students Test",
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
            for payment in db.scalars(
                select(Payment).where(Payment.cohort_id == cohort.id)
            ).all():
                db.delete(payment)
            accounts = list(
                db.scalars(
                    select(StudentBillingAccount).where(
                        StudentBillingAccount.cohort_id == cohort.id
                    )
                ).all()
            )
            for account in accounts:
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
            select(User).where(User.email.like("admin-students-%@example.com"))
        ).all():
            db.delete(user)
        for user in db.scalars(
            select(User).where(User.email.like("students-test-%@example.com"))
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
            name="Admin Students Test Cohort",
            slug=COHORT_SLUG,
            description="admin students tests",
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


def _installment_plan(db, cohort: Cohort) -> TuitionPlan:
    return TuitionPlanService(db).create_plan(
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


def _create_account(db, cohort: Cohort, student: User, state: str) -> StudentBillingAccount:
    plan = _installment_plan(db, cohort)
    account = BillingAccountService(db).create_account(
        student=student, tuition_plan_id=plan.id, cohort_id=cohort.id
    )
    obligations = sorted(account.obligations, key=lambda o: o.sequence_number)
    if state == "unpaid":
        pass
    elif state == "partial":
        obligations[0].status = ObligationStatus.PAID
        obligations[0].paid_amount = obligations[0].amount_due
        obligations[0].paid_at = datetime.now(UTC)
        obligations[1].status = ObligationStatus.OPEN
        account.amount_paid = money(obligations[0].amount_due)
        account.amount_outstanding = money(account.final_amount_due - account.amount_paid)
        account.billing_status = BillingStatus.CURRENT
    elif state == "paid":
        for obligation in obligations:
            obligation.status = ObligationStatus.PAID
            obligation.paid_amount = obligation.amount_due
            obligation.paid_at = datetime.now(UTC)
        account.amount_paid = account.final_amount_due
        account.amount_outstanding = Decimal("0.00")
        account.billing_status = BillingStatus.PAID_IN_FULL
    db.commit()
    db.refresh(account)
    return account


def _make_payment(db, cohort: Cohort, user: User, amount: int) -> Payment:
    payment = Payment(
        order_id=f"test-{uuid.uuid4().hex[:12]}",
        user_id=user.id,
        cohort_id=cohort.id,
        provider=PaymentProviderName.MOCK,
        provider_payment_id=f"mock_{uuid.uuid4().hex[:8]}",
        amount=amount,
        currency=cohort.currency,
        status=PaymentStatus.CONFIRMED,
        confirmed_at=datetime.now(UTC),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@pytest.fixture
def students_env():
    _cleanup()
    cohort = _seed_cohort()
    yield cohort
    _cleanup()


def test_admin_students_requires_admin(students_env):
    student = _make_user("students-test")
    try:
        assert client.get("/api/v1/admin/students", headers=_auth(student)).status_code == 403
        assert client.get("/api/v1/admin/installments", headers=_auth(student)).status_code == 403
    finally:
        _cleanup()


def test_list_students_classifies_paid_partial_unpaid(students_env):
    db = SessionLocal()
    try:
        paid = _make_user("students-test")
        partial = _make_user("students-test")
        unpaid = _make_user("students-test")
        _create_account(db, students_env, paid, "paid")
        _create_account(db, students_env, partial, "partial")
        _create_account(db, students_env, unpaid, "unpaid")
        _make_payment(db, students_env, paid, students_env.price)
        _make_payment(db, students_env, partial, students_env.price // 2)

        result = AdminStudentsService(db).list_students(cohort_id=students_env.id)
        by_id = {row.user_id: row for row in result.rows}
        assert by_id[paid.id].payment_status == "paid"
        assert by_id[partial.id].payment_status == "partial"
        # Unpaid / pending-only students are excluded from the paid roster.
        assert unpaid.id not in by_id
        assert by_id[partial.id].has_outstanding is True
        assert by_id[paid.id].has_outstanding is False
        assert result.total == 2
        assert result.paid == 1 and result.partial == 1 and result.unpaid == 0
    finally:
        db.close()


def test_list_students_filters(students_env):
    db = SessionLocal()
    try:
        paid = _make_user("students-test")
        partial = _make_user("students-test")
        _create_account(db, students_env, paid, "paid")
        _create_account(db, students_env, partial, "partial")
        _make_payment(db, students_env, paid, students_env.price)
        _make_payment(db, students_env, partial, students_env.price // 2)
        service = AdminStudentsService(db)

        paid_only = service.list_students(cohort_id=students_env.id, payment_status="paid")
        assert paid_only.paid == 1 and paid_only.unpaid == 0

        outstanding = service.list_students(cohort_id=students_env.id, has_outstanding=True)
        assert all(row.has_outstanding for row in outstanding.rows)
        assert outstanding.total == 1

        installments = service.list_students(cohort_id=students_env.id, plan="installments")
        assert installments.total == 2

        # Admin endpoint returns the same shape.
        admin = _make_user("admin-students", UserRole.ADMIN)
        response = client.get(
            "/api/v1/admin/students",
            headers=_auth(admin),
            params={"cohort_id": str(students_env.id), "payment_status": "paid"},
        )
        assert response.status_code == 200
        assert response.json()["paid"] == 1
    finally:
        db.close()


def test_list_installments_buckets(students_env):
    db = SessionLocal()
    try:
        student = _make_user("students-test")
        account = _create_account(db, students_env, student, "unpaid")
        obligations = sorted(account.obligations, key=lambda o: o.sequence_number)
        now = datetime.now(UTC)
        # Overdue
        obligations[0].due_date = now - timedelta(days=2)
        obligations[0].status = ObligationStatus.OPEN
        # Due soon
        obligations[1].due_date = now + timedelta(days=1)
        obligations[1].status = ObligationStatus.OPEN
        db.commit()

        service = AdminStudentsService(db)
        rows = service.list_installments(cohort_id=students_env.id)
        by_id = {r.obligation_id: r for r in rows}
        assert by_id[obligations[0].id].bucket == "overdue"
        assert by_id[obligations[1].id].bucket == "due_soon"

        overdue = service.list_installments(cohort_id=students_env.id, status_filter="overdue")
        assert {r.obligation_id for r in overdue} == {obligations[0].id}

        admin = _make_user("admin-students", UserRole.ADMIN)
        response = client.get(
            "/api/v1/admin/installments",
            headers=_auth(admin),
            params={"cohort_id": str(students_env.id), "status": "overdue"},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
    finally:
        db.close()


def test_instructors_are_not_counted_as_students(students_env):
    """Cohort membership includes staff roles — the student roster must ignore them."""
    db = SessionLocal()
    try:
        instructor = _make_user("students-test", UserRole.INSTRUCTOR)
        student = _make_user("students-test")
        db.add(
            CohortMember(
                cohort_id=students_env.id,
                user_id=instructor.id,
                role=CohortMemberRole.INSTRUCTOR,
            )
        )
        db.add(
            CohortMember(
                cohort_id=students_env.id,
                user_id=student.id,
                role=CohortMemberRole.STUDENT,
            )
        )
        db.commit()
        _make_payment(db, students_env, student, students_env.price)

        result = AdminStudentsService(db).list_students(cohort_id=students_env.id)
        ids = {row.user_id for row in result.rows}
        assert student.id in ids
        assert instructor.id not in ids
        assert result.total == 1
    finally:
        db.close()


def test_installments_board_ignores_settled_obligations(students_env):
    """Reminders target money still owed — fully paid accounts stay off the board."""
    db = SessionLocal()
    try:
        student = _make_user("students-test")
        account = _create_account(db, students_env, student, "paid")
        service = AdminStudentsService(db)

        assert service.list_installments(cohort_id=students_env.id) == []

        settled = service.list_installments(cohort_id=students_env.id, status_filter="paid")
        assert {row.obligation_id for row in settled} == {
            obligation.id for obligation in account.obligations
        }
    finally:
        db.close()