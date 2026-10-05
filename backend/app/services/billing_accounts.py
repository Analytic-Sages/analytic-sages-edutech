from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.billing import BillingStatus, DueRule, ObligationStatus
from app.core.payments import PaymentStatus
from app.core.roles import UserRole
from app.models.billing import (
    BillingAuditEvent,
    PaymentObligation,
    StudentBillingAccount,
    TuitionPlan,
)
from app.models.classroom import Cohort, CohortMember
from app.models.payment import Payment
from app.models.user import User
from app.services.tuition_plans import TuitionPlanService, money


class BillingAccountService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.plans = TuitionPlanService(db)

    def create_account(
        self,
        *,
        student: User,
        tuition_plan_id: UUID,
        cohort_id: UUID | None = None,
        course_id: UUID | None = None,
        actor: User | None = None,
    ) -> StudentBillingAccount:
        plan = self.plans.get_plan(tuition_plan_id)
        if not plan.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Tuition plan is not active"
            )

        resolved_cohort_id = cohort_id or plan.cohort_id
        resolved_course_id = course_id or plan.course_id
        if not resolved_cohort_id and not resolved_course_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tuition plan must be attached to a cohort or course",
            )

        cohort = None
        if resolved_cohort_id:
            cohort = self.db.get(Cohort, resolved_cohort_id)
            if not cohort:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")
            if plan.cohort_id and plan.cohort_id != resolved_cohort_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Plan does not apply to this cohort",
                )
            member = self.db.scalar(
                select(CohortMember).where(
                    CohortMember.cohort_id == cohort.id,
                    CohortMember.user_id == student.id,
                )
            )
            if member:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You are already registered for this cohort",
                )

        existing = self._find_open_account(
            student_id=student.id,
            cohort_id=resolved_cohort_id,
            course_id=resolved_course_id,
        )
        if existing:
            if existing.tuition_plan_id == plan.id:
                return self.get_account(existing.id, student_id=student.id)
            if self._has_started_paying(existing):
                # Money already moved on the old plan — changing it is a refund/
                # adjustment decision, so hand it to support instead of guessing.
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "You already started paying on a different tuition plan for this "
                        "enrollment. Contact support to change your plan."
                    ),
                )
            # Nothing has been paid yet, so honor the change of mind and switch
            # the existing account to the plan they picked now.
            return self._switch_plan(
                account=existing,
                plan=plan,
                cohort=cohort,
                student=student,
                actor=actor,
            )

        total = money(plan.base_amount)
        account = StudentBillingAccount(
            student_id=student.id,
            course_id=resolved_course_id or (cohort.course_id if cohort else None),
            cohort_id=resolved_cohort_id,
            tuition_plan_id=plan.id,
            currency=plan.base_currency,
            total_amount=total,
            discount_amount=Decimal("0.00"),
            scholarship_amount=Decimal("0.00"),
            final_amount_due=total,
            amount_paid=Decimal("0.00"),
            amount_outstanding=total,
            billing_status=BillingStatus.PENDING,
        )
        self.db.add(account)
        self.db.flush()

        self._add_obligations(account, plan, cohort)

        self._audit(
            actor_id=(actor or student).id,
            action="billing_account.created",
            entity_type="student_billing_account",
            entity_id=account.id,
            after={"tuition_plan_id": str(plan.id), "final_amount_due": str(total)},
        )
        self.db.commit()
        return self.get_account(account.id, student_id=student.id)

    def get_account(
        self, account_id: UUID, *, student_id: UUID | None = None
    ) -> StudentBillingAccount:
        stmt = (
            select(StudentBillingAccount)
            .options(
                selectinload(StudentBillingAccount.obligations),
                selectinload(StudentBillingAccount.tuition_plan).selectinload(
                    TuitionPlan.schedules
                ),
            )
            .where(StudentBillingAccount.id == account_id)
        )
        account = self.db.scalar(stmt)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Billing account not found"
            )
        if student_id is not None and account.student_id != student_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Billing account not found"
            )
        return account

    def list_for_student(self, student_id: UUID) -> list[StudentBillingAccount]:
        return list(
            self.db.scalars(
                select(StudentBillingAccount)
                .options(
                    selectinload(StudentBillingAccount.obligations),
                    selectinload(StudentBillingAccount.tuition_plan),
                )
                .where(StudentBillingAccount.student_id == student_id)
                .order_by(StudentBillingAccount.created_at.desc())
            ).all()
        )

    def list_admin(
        self,
        *,
        status_filter: BillingStatus | None = None,
        cohort_id: UUID | None = None,
        limit: int = 100,
    ) -> list[StudentBillingAccount]:
        stmt = (
            select(StudentBillingAccount)
            .join(User, StudentBillingAccount.student_id == User.id)
            .options(
                selectinload(StudentBillingAccount.obligations),
                selectinload(StudentBillingAccount.tuition_plan),
            )
            .where(User.role == UserRole.STUDENT)
            .order_by(StudentBillingAccount.created_at.desc())
            .limit(limit)
        )
        if status_filter:
            stmt = stmt.where(StudentBillingAccount.billing_status == status_filter)
        if cohort_id:
            stmt = stmt.where(StudentBillingAccount.cohort_id == cohort_id)
        return list(self.db.scalars(stmt).all())

    def update_status(
        self,
        *,
        account_id: UUID,
        billing_status: BillingStatus,
        actor: User,
        note: str | None = None,
    ) -> StudentBillingAccount:
        account = self.get_account(account_id)
        before = account.billing_status.value
        account.billing_status = billing_status
        self._audit(
            actor_id=actor.id,
            action="billing_account.status_updated",
            entity_type="student_billing_account",
            entity_id=account.id,
            note=note,
            before={"billing_status": before},
            after={"billing_status": billing_status.value},
        )
        self.db.commit()
        return self.get_account(account.id)

    def extend_next_due(
        self,
        *,
        account_id: UUID,
        due_date: datetime,
        actor: User,
        note: str | None = None,
    ) -> StudentBillingAccount:
        """Set a custom date on the student's next open installment obligation."""
        account = self.get_account(account_id)
        open_obligations = sorted(
            [
                o
                for o in account.obligations
                if o.status
                in {
                    ObligationStatus.OPEN,
                    ObligationStatus.PAST_DUE,
                    ObligationStatus.PROCESSING,
                    ObligationStatus.UPCOMING,
                }
            ],
            key=lambda o: o.sequence_number,
        )
        if not open_obligations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No open installment to reschedule",
            )
        obligation = open_obligations[0]
        before = obligation.due_date.isoformat() if obligation.due_date else None
        obligation.due_date = due_date
        if obligation.status == ObligationStatus.PAST_DUE and due_date > datetime.now(UTC):
            obligation.status = ObligationStatus.OPEN
        self._audit(
            actor_id=actor.id,
            action="obligation.extended",
            entity_type="payment_obligation",
            entity_id=obligation.id,
            note=note,
            before={"due_date": before},
            after={"due_date": due_date.isoformat()},
        )
        self.db.commit()
        return self.get_account(account.id)

    def set_access_blocked(
        self,
        *,
        account_id: UUID,
        access_blocked: bool,
        actor: User,
        note: str | None = None,
    ) -> StudentBillingAccount:
        """Manually restrict / restore a student's live-session access."""
        account = self.get_account(account_id)
        before = account.access_blocked
        account.access_blocked = access_blocked
        self._audit(
            actor_id=actor.id,
            action="billing_account.access_blocked"
            if access_blocked
            else "billing_account.access_unblocked",
            entity_type="student_billing_account",
            entity_id=account.id,
            note=note,
            before={"access_blocked": before},
            after={"access_blocked": access_blocked},
        )
        self.db.commit()
        return self.get_account(account.id)

    def _find_open_account(
        self,
        *,
        student_id: UUID,
        cohort_id: UUID | None,
        course_id: UUID | None,
    ) -> StudentBillingAccount | None:
        stmt = select(StudentBillingAccount).where(
            StudentBillingAccount.student_id == student_id,
            StudentBillingAccount.billing_status.notin_(
                {
                    BillingStatus.CANCELLED,
                    BillingStatus.REFUNDED,
                    BillingStatus.PAID_IN_FULL,
                }
            ),
        )
        if cohort_id:
            stmt = stmt.where(StudentBillingAccount.cohort_id == cohort_id)
        elif course_id:
            stmt = stmt.where(StudentBillingAccount.course_id == course_id)
        else:
            return None
        return self.db.scalar(stmt)

    def _has_started_paying(self, account: StudentBillingAccount) -> bool:
        """True once any money is confirmed against the account.

        Until then a student is free to change which plan they want, because
        nothing has actually been charged against the current schedule.
        """
        if money(account.amount_paid) > Decimal("0.00"):
            return True
        return (
            self.db.scalar(
                select(Payment.id)
                .where(
                    Payment.billing_account_id == account.id,
                    Payment.status == PaymentStatus.CONFIRMED,
                )
                .limit(1)
            )
            is not None
        )

    def _add_obligations(
        self,
        account: StudentBillingAccount,
        plan: TuitionPlan,
        cohort: Cohort | None,
    ) -> None:
        for schedule in sorted(plan.schedules, key=lambda s: s.sequence_number):
            is_first = schedule.sequence_number == 1
            self.db.add(
                PaymentObligation(
                    billing_account_id=account.id,
                    sequence_number=schedule.sequence_number,
                    description=schedule.label or f"Installment {schedule.sequence_number}",
                    amount_due=money(schedule.amount),
                    currency=plan.base_currency,
                    due_date=self._resolve_due_date(schedule.due_rule, schedule, cohort),
                    status=ObligationStatus.OPEN if is_first else ObligationStatus.UPCOMING,
                )
            )

    def _switch_plan(
        self,
        *,
        account: StudentBillingAccount,
        plan: TuitionPlan,
        cohort: Cohort | None,
        student: User,
        actor: User | None = None,
    ) -> StudentBillingAccount:
        """Move an unpaid account onto a different plan for the same enrollment.

        Only reached before the first confirmed payment. We keep the same
        account row (so nothing downstream loses its reference), expire any
        unfinished checkout tied to the plan we're leaving, and rebuild the
        schedule so the student can pay the option they actually chose.
        """
        before = {
            "tuition_plan_id": str(account.tuition_plan_id),
            "final_amount_due": str(account.final_amount_due),
            "amount_outstanding": str(account.amount_outstanding),
        }

        # Expire in-flight checkouts for the abandoned plan so a late provider
        # callback can't confirm against a schedule the student walked away from.
        inflight = list(
            self.db.scalars(
                select(Payment).where(
                    Payment.billing_account_id == account.id,
                    Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.CONFIRMING]),
                )
            ).all()
        )
        for payment in inflight:
            payment.status = PaymentStatus.EXPIRED
            payment.payment_obligation_id = None

        # Rebuild obligations for the new plan (the old schedule no longer applies).
        for obligation in list(account.obligations):
            self.db.delete(obligation)
        self.db.flush()

        total = money(plan.base_amount)
        account.tuition_plan_id = plan.id
        account.currency = plan.base_currency
        account.total_amount = total
        account.discount_amount = Decimal("0.00")
        account.scholarship_amount = Decimal("0.00")
        account.final_amount_due = total
        account.amount_outstanding = money(total - account.amount_paid)
        account.billing_status = BillingStatus.PENDING
        self.db.flush()

        self._add_obligations(account, plan, cohort)
        self._audit(
            actor_id=(actor or student).id,
            action="billing_account.plan_switched",
            entity_type="student_billing_account",
            entity_id=account.id,
            after={"tuition_plan_id": str(plan.id), "final_amount_due": str(total)},
            before=before,
        )
        self.db.commit()
        return self.get_account(account.id, student_id=student.id)

    def _resolve_due_date(
        self,
        due_rule: DueRule,
        schedule,
        cohort: Cohort | None,
    ) -> datetime | None:
        now = datetime.now(UTC)
        if due_rule == DueRule.IMMEDIATE:
            return now
        if due_rule == DueRule.SPECIFIC_DATE:
            return schedule.due_date
        if due_rule == DueRule.BEFORE_COHORT_START:
            if not cohort or not cohort.starts_at:
                return schedule.due_date
            offset = schedule.offset_days or 0
            return cohort.starts_at - timedelta(days=offset)
        if due_rule == DueRule.WEEK_NUMBER:
            if not cohort or not cohort.starts_at:
                return schedule.due_date
            week = schedule.week_number or 1
            return cohort.starts_at + timedelta(weeks=max(week - 1, 0))
        return schedule.due_date

    def _audit(
        self,
        *,
        actor_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: UUID,
        note: str | None = None,
        before: dict | None = None,
        after: dict | None = None,
    ) -> None:
        self.db.add(
            BillingAuditEvent(
                actor_id=actor_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                note=note,
                before_json=before,
                after_json=after,
            )
        )
