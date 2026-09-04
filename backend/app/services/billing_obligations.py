from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.billing import BillingStatus, ObligationStatus
from app.models.billing import BillingAuditEvent, PaymentObligation, StudentBillingAccount
from app.models.user import User
from app.services.tuition_plans import money


class PaymentObligationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_obligation(
        self, obligation_id: UUID, *, student_id: UUID | None = None
    ) -> PaymentObligation:
        stmt = (
            select(PaymentObligation)
            .options(selectinload(PaymentObligation.billing_account))
            .where(PaymentObligation.id == obligation_id)
        )
        obligation = self.db.scalar(stmt)
        if not obligation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Payment obligation not found"
            )
        if student_id is not None and obligation.billing_account.student_id != student_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Payment obligation not found"
            )
        return obligation

    def get_payable_obligation(
        self, obligation_id: UUID, *, student_id: UUID
    ) -> PaymentObligation:
        obligation = self.get_obligation(obligation_id, student_id=student_id)
        account = obligation.billing_account
        if account.billing_status in {
            BillingStatus.CANCELLED,
            BillingStatus.REFUNDED,
            BillingStatus.PAYMENT_HOLD,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This billing account cannot accept payments right now",
            )
        if obligation.status not in {
            ObligationStatus.OPEN,
            ObligationStatus.PAST_DUE,
            ObligationStatus.PROCESSING,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This installment is not open for payment",
            )
        return obligation

    def open_next_obligation(self, account: StudentBillingAccount) -> PaymentObligation | None:
        upcoming = sorted(
            [
                o
                for o in account.obligations
                if o.status == ObligationStatus.UPCOMING
            ],
            key=lambda o: o.sequence_number,
        )
        if not upcoming:
            return None
        nxt = upcoming[0]
        nxt.status = ObligationStatus.OPEN
        return nxt

    def mark_overdue(self, *, as_of: datetime | None = None) -> int:
        now = as_of or datetime.now(UTC)
        rows = list(
            self.db.scalars(
                select(PaymentObligation).where(
                    PaymentObligation.status == ObligationStatus.OPEN,
                    PaymentObligation.due_date.is_not(None),
                    PaymentObligation.due_date < now,
                )
            ).all()
        )
        for row in rows:
            row.status = ObligationStatus.PAST_DUE
            account = self.db.get(StudentBillingAccount, row.billing_account_id)
            if account and account.billing_status in {
                BillingStatus.PENDING,
                BillingStatus.CURRENT,
            }:
                account.billing_status = BillingStatus.PAST_DUE
        if rows:
            self.db.commit()
        return len(rows)

    def waive(
        self,
        *,
        obligation_id: UUID,
        actor: User,
        note: str | None = None,
    ) -> PaymentObligation:
        obligation = self.get_obligation(obligation_id)
        if obligation.status == ObligationStatus.PAID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Obligation already paid"
            )
        before = obligation.status.value
        obligation.status = ObligationStatus.WAIVED
        obligation.paid_amount = money(obligation.amount_due)
        obligation.paid_at = datetime.now(UTC)
        account = self.db.get(StudentBillingAccount, obligation.billing_account_id)
        if account:
            account.amount_outstanding = money(
                max(Decimal("0.00"), account.amount_outstanding - obligation.amount_due)
            )
            if account.amount_outstanding <= Decimal("0.00"):
                account.billing_status = BillingStatus.PAID_IN_FULL
                account.amount_outstanding = Decimal("0.00")
            else:
                self.open_next_obligation(account)
                if account.billing_status == BillingStatus.PENDING:
                    account.billing_status = BillingStatus.CURRENT
        self.db.add(
            BillingAuditEvent(
                actor_id=actor.id,
                action="obligation.waived",
                entity_type="payment_obligation",
                entity_id=obligation.id,
                note=note,
                before_json={"status": before},
                after_json={"status": ObligationStatus.WAIVED.value},
            )
        )
        self.db.commit()
        return self.get_obligation(obligation.id)

    def extend_due_date(
        self,
        *,
        obligation_id: UUID,
        due_date: datetime,
        actor: User,
        note: str | None = None,
    ) -> PaymentObligation:
        obligation = self.get_obligation(obligation_id)
        before = obligation.due_date.isoformat() if obligation.due_date else None
        obligation.due_date = due_date
        if obligation.status == ObligationStatus.PAST_DUE and due_date > datetime.now(UTC):
            obligation.status = ObligationStatus.OPEN
        self.db.add(
            BillingAuditEvent(
                actor_id=actor.id,
                action="obligation.extended",
                entity_type="payment_obligation",
                entity_id=obligation.id,
                note=note,
                before_json={"due_date": before},
                after_json={"due_date": due_date.isoformat()},
            )
        )
        self.db.commit()
        return self.get_obligation(obligation.id)
