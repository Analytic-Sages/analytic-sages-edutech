from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.billing import BillingStatus, ObligationStatus
from app.core.payments import PaymentStatus
from app.models.billing import (
    BillingAuditEvent,
    PaymentObligation,
    PaymentWebhookEvent,
    StudentBillingAccount,
)
from app.models.payment import Payment
from app.services.billing_obligations import PaymentObligationService
from app.services.tuition_plans import money


class BillingReconciliationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.obligations = PaymentObligationService(db)

    def record_webhook_event(
        self,
        *,
        provider: str,
        event_key: str,
        payment_id: UUID | None,
        payload: dict | None = None,
    ) -> bool:
        """Return True if this is a new event; False if already processed (dedupe)."""
        existing = self.db.scalar(
            select(PaymentWebhookEvent).where(
                PaymentWebhookEvent.provider == provider,
                PaymentWebhookEvent.event_key == event_key,
            )
        )
        if existing:
            return False
        payload_hash = None
        if payload is not None:
            raw = json.dumps(payload, sort_keys=True, default=str).encode()
            payload_hash = hashlib.sha256(raw).hexdigest()
        self.db.add(
            PaymentWebhookEvent(
                provider=provider,
                event_key=event_key,
                payment_id=payment_id,
                payload_hash=payload_hash,
            )
        )
        self.db.flush()
        return True

    def reconcile_confirmed_payment(self, payment: Payment) -> StudentBillingAccount | None:
        if payment.status != PaymentStatus.CONFIRMED:
            return None
        if not payment.payment_obligation_id:
            return None

        obligation = self.db.scalar(
            select(PaymentObligation)
            .options(
                selectinload(PaymentObligation.billing_account).selectinload(
                    StudentBillingAccount.obligations
                )
            )
            .where(PaymentObligation.id == payment.payment_obligation_id)
            .with_for_update()
        )
        if not obligation:
            return None

        account = obligation.billing_account
        if obligation.status == ObligationStatus.PAID:
            return account

        allocated = money(payment.amount)
        obligation.paid_amount = allocated
        obligation.paid_at = payment.confirmed_at or datetime.now(UTC)
        obligation.status = ObligationStatus.PAID

        account.amount_paid = money(account.amount_paid + allocated)
        account.amount_outstanding = money(
            max(Decimal("0.00"), account.final_amount_due - account.amount_paid)
        )

        remaining = [
            o
            for o in account.obligations
            if o.id != obligation.id
            and o.status
            not in {
                ObligationStatus.PAID,
                ObligationStatus.WAIVED,
                ObligationStatus.CANCELLED,
            }
        ]
        if not remaining and account.amount_outstanding <= Decimal("0.00"):
            account.billing_status = BillingStatus.PAID_IN_FULL
            account.amount_outstanding = Decimal("0.00")
        else:
            self.obligations.open_next_obligation(account)
            if account.billing_status in {BillingStatus.PENDING, BillingStatus.PAST_DUE}:
                account.billing_status = BillingStatus.CURRENT

        self.db.add(
            BillingAuditEvent(
                actor_id=None,
                action="obligation.paid",
                entity_type="payment_obligation",
                entity_id=obligation.id,
                after_json={
                    "payment_id": str(payment.id),
                    "paid_amount": str(allocated),
                    "account_status": account.billing_status.value,
                },
            )
        )
        self.db.flush()
        return account

    def first_obligation_paid(self, account: StudentBillingAccount) -> bool:
        first = next(
            (o for o in account.obligations if o.sequence_number == 1),
            None,
        )
        return bool(first and first.status == ObligationStatus.PAID)
