"""Installment reminder emails — manual (admin) and scheduled.

Database-backed and idempotent: an obligation is reminded once, then optionally
re-nagged after a cool-down while it stays unpaid. Safe to call repeatedly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.billing import ObligationStatus
from app.models.billing import PaymentObligation, StudentBillingAccount
from app.models.classroom import Cohort
from app.models.course import Course
from app.models.user import User
from app.services.email import EmailService

logger = logging.getLogger(__name__)

# Obligations that still owe money (and therefore merit reminders).
REMINDABLE_STATUSES = (
    ObligationStatus.UPCOMING,
    ObligationStatus.OPEN,
    ObligationStatus.PROCESSING,
    ObligationStatus.PAST_DUE,
)
# Re-nag an unpaid, overdue obligation no more often than this.
RESEND_AFTER_DAYS = 3


@dataclass
class ReminderOutcome:
    sent: int = 0
    skipped: int = 0
    failed: int = 0

    def as_dict(self) -> dict[str, int]:
        return {"sent": self.sent, "skipped": self.skipped, "failed": self.failed}


class BillingReminderService:
    def __init__(self, db: Session, email_service: EmailService, *, lead_days: int = 3) -> None:
        self.db = db
        self.email_service = email_service
        self.lead_days = lead_days

    def _title_for(self, account: StudentBillingAccount) -> str:
        if account.cohort_id:
            cohort = self.db.get(Cohort, account.cohort_id)
            if cohort:
                return cohort.name
        if account.course_id:
            course = self.db.get(Course, account.course_id)
            if course:
                return course.title
        return "Your tuition plan"

    @staticmethod
    def reminder_kind(obligation: PaymentObligation, now: datetime) -> str | None:
        """due_soon | due_today | overdue | None (when not time to remind yet)."""
        due = obligation.due_date
        if due is None:
            return "due_soon" if obligation.status == ObligationStatus.OPEN else None
        if due.tzinfo is None:
            due = due.replace(tzinfo=UTC)
        if due < now:
            return "overdue"
        if due.date() == now.date():
            return "due_today"
        return "due_soon"

    def _should_send(self, obligation: PaymentObligation, kind: str, now: datetime) -> bool:
        if obligation.reminder_sent_at is None:
            return True
        sent = obligation.reminder_sent_at
        if sent.tzinfo is None:
            sent = sent.replace(tzinfo=UTC)
        # Non-overdue reminders are one-shot; overdue ones re-send after cool-down.
        if kind != "overdue":
            return False
        return now - sent >= timedelta(days=RESEND_AFTER_DAYS)

    def _dispatch(self, obligation: PaymentObligation, kind: str) -> bool:
        account = obligation.billing_account
        user = self.db.get(User, account.student_id)
        if not user:
            return False
        sent = self.email_service.send_installment_reminder(
            email=user.email,
            student_name=user.full_name,
            title=self._title_for(account),
            sequence_number=obligation.sequence_number,
            installments_total=len(account.obligations),
            amount=obligation.amount_due,
            currency=obligation.currency,
            due_date=obligation.due_date,
            kind=kind,
        )
        return bool(sent)

    # ---------- public API ----------

    def remind_obligation(self, obligation_id: UUID) -> bool:
        obligation = self.db.scalar(
            select(PaymentObligation)
            .options(
                selectinload(PaymentObligation.billing_account).selectinload(
                    StudentBillingAccount.obligations
                )
            )
            .where(PaymentObligation.id == obligation_id)
        )
        if not obligation or obligation.status not in REMINDABLE_STATUSES:
            return False
        now = datetime.now(UTC)
        kind = self.reminder_kind(obligation, now) or "due_soon"
        sent = self._dispatch(obligation, kind)
        if sent:
            obligation.reminder_sent_at = now
            self.db.commit()
        return sent

    def run(
        self,
        *,
        scope: str = "all",
        cohort_id: UUID | None = None,
        limit: int = 500,
    ) -> ReminderOutcome:
        """Send due reminders. ``scope`` = all | overdue | due_soon."""
        now = datetime.now(UTC)
        cutoff = now + timedelta(days=self.lead_days)
        stmt = (
            select(PaymentObligation)
            .options(
                selectinload(PaymentObligation.billing_account).selectinload(
                    StudentBillingAccount.obligations
                )
            )
            .where(PaymentObligation.status.in_(REMINDABLE_STATUSES))
            .order_by(PaymentObligation.due_date.asc().nulls_last())
            .limit(limit)
        )
        if cohort_id:
            stmt = (
                stmt.join(StudentBillingAccount)
                .where(StudentBillingAccount.cohort_id == cohort_id)
            )
        obligations = list(self.db.scalars(stmt).all())

        outcome = ReminderOutcome()
        for obligation in obligations:
            kind = self.reminder_kind(obligation, now)
            if kind is None:
                outcome.skipped += 1
                continue
            if scope == "overdue" and kind != "overdue":
                outcome.skipped += 1
                continue
            if scope == "due_soon" and kind not in {"due_soon", "due_today"}:
                outcome.skipped += 1
                continue
            due = obligation.due_date
            if due is not None:
                if due.tzinfo is None:
                    due = due.replace(tzinfo=UTC)
                if kind != "overdue" and due > cutoff:
                    outcome.skipped += 1
                    continue
            if not self._should_send(obligation, kind, now):
                outcome.skipped += 1
                continue
            try:
                if self._dispatch(obligation, kind):
                    obligation.reminder_sent_at = now
                    outcome.sent += 1
                else:
                    outcome.failed += 1
            except Exception:
                logger.exception("Installment reminder failed for obligation %s", obligation.id)
                outcome.failed += 1

        if outcome.sent:
            self.db.commit()
        return outcome
        return bool(sent)