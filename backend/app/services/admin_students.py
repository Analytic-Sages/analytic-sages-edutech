"""Admin views over students and their payment / installment status.

Powers "who has paid vs not" and the installment collections board. Derived from
billing accounts + obligations + confirmed payments so admins can chase tuition
without a developer.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.billing import ObligationStatus, TuitionPlanType
from app.core.payments import EnrollmentStatus, PaymentStatus
from app.core.roles import UserRole
from app.models.billing import PaymentObligation, StudentBillingAccount
from app.models.classroom import Cohort, CohortMember, CohortMemberRole
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.payment import Payment
from app.models.user import User
from app.schemas.admin_students import (
    AdminInstallmentRow,
    AdminStudentList,
    AdminStudentRow,
)

# Obligations with these statuses still owe money.
OPEN_OBLIGATION_STATUSES = (
    ObligationStatus.UPCOMING,
    ObligationStatus.OPEN,
    ObligationStatus.PROCESSING,
    ObligationStatus.PAST_DUE,
)
PAID_OBLIGATION_STATUSES = (ObligationStatus.PAID, ObligationStatus.WAIVED)
INSTALLMENT_PLAN_TYPES = (TuitionPlanType.INSTALLMENT, TuitionPlanType.MONTHLY)
PLAN_FILTER_FULL = "full"
PLAN_FILTER_INSTALLMENTS = "installments"


class AdminStudentsService:
    def __init__(self, db: Session, *, reminder_lead_days: int = 3) -> None:
        self.db = db
        self.reminder_lead_days = reminder_lead_days

    # ---------- shared helpers ----------

    def _accounts_for_users(
        self, user_ids: set[UUID]
    ) -> dict[UUID, list[StudentBillingAccount]]:
        if not user_ids:
            return {}
        accounts = list(
            self.db.scalars(
                select(StudentBillingAccount)
                .options(
                    selectinload(StudentBillingAccount.obligations),
                    selectinload(StudentBillingAccount.tuition_plan),
                )
                .where(StudentBillingAccount.student_id.in_(user_ids))
            ).all()
        )
        grouped: dict[UUID, list[StudentBillingAccount]] = {}
        for account in accounts:
            grouped.setdefault(account.student_id, []).append(account)
        return grouped

    def _confirmed_paid(self, user_ids: set[UUID]) -> dict[UUID, Decimal]:
        if not user_ids:
            return {}
        rows = self.db.execute(
            select(Payment.user_id, func.coalesce(func.sum(Payment.amount), 0))
            .where(
                Payment.user_id.in_(user_ids),
                Payment.status == PaymentStatus.CONFIRMED,
            )
            .group_by(Payment.user_id)
        ).all()
        return {user_id: Decimal(str(total or 0)) for user_id, total in rows}

    def _cohort_names(self, cohort_ids: set[UUID]) -> dict[UUID, str]:
        if not cohort_ids:
            return {}
        rows = self.db.execute(
            select(Cohort.id, Cohort.name).where(Cohort.id.in_(cohort_ids))
        ).all()
        return {cohort_id: name for cohort_id, name in rows}

    def _course_titles(self, course_ids: set[UUID]) -> dict[UUID, str]:
        if not course_ids:
            return {}
        rows = self.db.execute(
            select(Course.id, Course.title).where(Course.id.in_(course_ids))
        ).all()
        return {course_id: title for course_id, title in rows}

    @staticmethod
    def _next_open_obligation(account: StudentBillingAccount) -> PaymentObligation | None:
        pending = [o for o in account.obligations if o.status in OPEN_OBLIGATION_STATUSES]
        if not pending:
            return None
        pending.sort(
            key=lambda o: (o.due_date or datetime.max.replace(tzinfo=UTC), o.sequence_number)
        )
        return pending[0]

    @staticmethod
    def _matches_plan_filter(accounts: list[StudentBillingAccount], plan: str) -> bool:
        if plan == "all" or not plan:
            return True
        # Users with no billing account count as "full" (one-time purchase / unused).
        if not accounts:
            return plan == PLAN_FILTER_FULL
        for account in accounts:
            plan_type = account.tuition_plan.plan_type if account.tuition_plan else None
            is_installment = plan_type in INSTALLMENT_PLAN_TYPES
            if plan == PLAN_FILTER_INSTALLMENTS and is_installment:
                return True
            if plan == PLAN_FILTER_FULL and not is_installment:
                return True
        return False

    def _build_row(
        self,
        user: User,
        accounts: list[StudentBillingAccount],
        *,
        confirmed_paid: Decimal,
        cohort_names: dict[UUID, str],
        course_titles: dict[UUID, str],
    ) -> AdminStudentRow:
        total_paid = sum((a.amount_paid for a in accounts), Decimal("0.00"))
        total_outstanding = sum((a.amount_outstanding for a in accounts), Decimal("0.00"))

        cohort_ids = {a.cohort_id for a in accounts if a.cohort_id}
        course_ids = {a.course_id for a in accounts if a.course_id}
        for enrollment_course_id in self.db.scalars(
            select(Enrollment.course_id).where(
                Enrollment.user_id == user.id,
                Enrollment.status.in_((EnrollmentStatus.ACTIVE, EnrollmentStatus.COMPLETED)),
            )
        ).all():
            course_ids.add(enrollment_course_id)
        for member_cohort_id in self.db.scalars(
            select(CohortMember.cohort_id).where(CohortMember.user_id == user.id)
        ).all():
            cohort_ids.add(member_cohort_id)

        currency = accounts[0].currency if accounts else None

        # Payment status: prefer billing accounts, fall back to confirmed payments.
        if accounts:
            if total_outstanding <= Decimal("0.00"):
                payment_status = "paid"
            elif total_paid > Decimal("0.00"):
                payment_status = "partial"
            else:
                payment_status = "unpaid"
        else:
            payment_status = "paid" if confirmed_paid > Decimal("0.00") else "unpaid"

        # Primary account for plan + next-due details: prefer one with money owed.
        primary = next(
            (a for a in accounts if a.amount_outstanding > Decimal("0.00")),
            accounts[0] if accounts else None,
        )
        next_obligation = self._next_open_obligation(primary) if primary else None
        plan_name = primary.tuition_plan.name if primary and primary.tuition_plan else None
        plan_type = (
            primary.tuition_plan.plan_type.value if primary and primary.tuition_plan else None
        )
        installments_total = len(primary.obligations) if primary else 0
        installments_paid = (
            sum(1 for o in primary.obligations if o.status in PAID_OBLIGATION_STATUSES)
            if primary
            else 0
        )

        return AdminStudentRow(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            cohorts=sorted({cohort_names[c] for c in cohort_ids if c in cohort_names}),
            courses=sorted({course_titles[c] for c in course_ids if c in course_titles}),
            plan_name=plan_name,
            plan_type=plan_type,
            payment_status=payment_status,
            currency=currency,
            amount_paid=total_paid,
            amount_outstanding=total_outstanding,
            installments_total=installments_total,
            installments_paid=installments_paid,
            next_due_date=next_obligation.due_date if next_obligation else None,
            next_due_amount=next_obligation.amount_due if next_obligation else None,
            next_due_status=next_obligation.status.value if next_obligation else None,
            has_outstanding=total_outstanding > Decimal("0.00"),
            billing_account_id=primary.id if primary else None,
            created_at=user.created_at,
        )

    # ---------- public queries ----------

    def list_students(
        self,
        *,
        payment_status: str = "all",
        plan: str = "all",
        cohort_id: UUID | None = None,
        has_outstanding: bool | None = None,
        q: str | None = None,
        limit: int = 500,
    ) -> AdminStudentList:
        user_ids: set[UUID] = set(
            self.db.scalars(select(StudentBillingAccount.student_id)).all()
        )
        # Instructors and TAs hold cohort membership too — only students belong on
        # this roster, so filter the membership ids down to student members.
        user_ids |= set(
            self.db.scalars(
                select(CohortMember.user_id).where(
                    CohortMember.role == CohortMemberRole.STUDENT
                )
            ).all()
        )
        user_ids |= set(
            self.db.scalars(
                select(Enrollment.user_id).where(
                    Enrollment.status.in_((EnrollmentStatus.ACTIVE, EnrollmentStatus.COMPLETED))
                )
            ).all()
        )

        users = (
            list(
                self.db.scalars(
                    select(User)
                    .where(User.id.in_(user_ids), User.role == UserRole.STUDENT)
                    .order_by(User.created_at.desc())
                ).all()
            )
            if user_ids
            else []
        )

        accounts_by_user = self._accounts_for_users(user_ids)
        confirmed = self._confirmed_paid(user_ids)
        cohort_names = self._cohort_names({c.id for c in self.db.scalars(select(Cohort)).all()})
        course_titles = self._course_titles({c.id for c in self.db.scalars(select(Course)).all()})

        needle = (q or "").strip().lower()
        rows: list[AdminStudentRow] = []
        for user in users:
            accounts = accounts_by_user.get(user.id, [])
            if cohort_id and not any(a.cohort_id == cohort_id for a in accounts):
                is_member = self.db.scalar(
                    select(CohortMember.id).where(
                        CohortMember.user_id == user.id,
                        CohortMember.cohort_id == cohort_id,
                    )
                )
                if not is_member:
                    continue
            row = self._build_row(
                user,
                accounts,
                confirmed_paid=confirmed.get(user.id, Decimal("0.00")),
                cohort_names=cohort_names,
                course_titles=course_titles,
            )
            if payment_status != "all" and row.payment_status != payment_status:
                continue
            if not self._matches_plan_filter(accounts, plan):
                continue
            if has_outstanding is not None and row.has_outstanding != has_outstanding:
                continue
            if needle and needle not in (row.email.lower() + " " + (row.full_name or "").lower()):
                continue
            rows.append(row)

        rows.sort(
            key=lambda r: (
                r.payment_status == "paid",  # unpaid + partial first
                r.next_due_date or datetime.max.replace(tzinfo=UTC),
                r.created_at,
            )
        )
        rows = rows[:limit]

        counts = {"paid": 0, "partial": 0, "unpaid": 0}
        for row in rows:
            counts[row.payment_status] = counts.get(row.payment_status, 0) + 1
        return AdminStudentList(
            rows=rows,
            total=len(rows),
            paid=counts["paid"],
            partial=counts["partial"],
            unpaid=counts["unpaid"],
        )

    def _obligation_bucket(self, obligation: PaymentObligation, now: datetime) -> str:
        if obligation.status in PAID_OBLIGATION_STATUSES:
            return "paid"
        due = obligation.due_date
        if due is None:
            return "upcoming"
        if due.tzinfo is None:
            due = due.replace(tzinfo=UTC)
        if due < now or obligation.status == ObligationStatus.PAST_DUE:
            return "overdue"
        if due <= now + timedelta(days=self.reminder_lead_days):
            return "due_soon"
        return "upcoming"

    def list_installments(
        self,
        *,
        status_filter: str = "all",
        cohort_id: UUID | None = None,
        limit: int = 500,
    ) -> list[AdminInstallmentRow]:
        now = datetime.now(UTC)
        stmt = (
            select(PaymentObligation)
            .options(
                selectinload(PaymentObligation.billing_account).selectinload(
                    StudentBillingAccount.tuition_plan
                )
            )
            .order_by(PaymentObligation.due_date.asc().nulls_last())
            .limit(limit)
        )
        obligations = list(self.db.scalars(stmt).all())

        user_ids = {o.billing_account.student_id for o in obligations}
        users = (
            {u.id: u for u in self.db.scalars(select(User).where(User.id.in_(user_ids))).all()}
            if user_ids
            else {}
        )
        cohort_names = self._cohort_names(
            {o.billing_account.cohort_id for o in obligations if o.billing_account.cohort_id}
        )
        course_titles = self._course_titles(
            {o.billing_account.course_id for o in obligations if o.billing_account.course_id}
        )

        rows: list[AdminInstallmentRow] = []
        for obligation in obligations:
            account = obligation.billing_account
            user = users.get(account.student_id)
            if not user:
                continue
            if cohort_id and account.cohort_id != cohort_id:
                continue
            bucket = self._obligation_bucket(obligation, now)
            if status_filter == "paid":
                if bucket != "paid":
                    continue
            elif bucket == "paid":
                # Settled installments (paid / waived) are not collectable, so they
                # never belong on the collections board — reminders only matter for
                # money still owed.
                continue
            elif status_filter in {"overdue", "due_soon", "upcoming"} and bucket != status_filter:
                continue
            due = obligation.due_date
            if due is not None and due.tzinfo is None:
                due = due.replace(tzinfo=UTC)
            days_until = (due - now).days if due else None
            plan = account.tuition_plan
            rows.append(
                AdminInstallmentRow(
                    obligation_id=obligation.id,
                    billing_account_id=account.id,
                    user_id=user.id,
                    email=user.email,
                    full_name=user.full_name,
                    cohort_name=cohort_names.get(account.cohort_id) if account.cohort_id else None,
                    course_title=course_titles.get(account.course_id) if account.course_id else None,
                    plan_name=plan.name if plan else None,
                    sequence_number=obligation.sequence_number,
                    installments_total=len(account.obligations),
                    description=obligation.description,
                    amount_due=obligation.amount_due,
                    currency=obligation.currency,
                    due_date=obligation.due_date,
                    status=obligation.status.value,
                    bucket=bucket,
                    days_until_due=days_until,
                    reminder_sent_at=obligation.reminder_sent_at,
                )
            )
        return rows