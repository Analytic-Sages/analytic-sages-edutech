from __future__ import annotations

import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.billing import ObligationStatus
from app.core.config import Settings
from app.core.payments import EnrollmentStatus, PaymentProviderName, PaymentStatus
from app.models.billing import PaymentObligation
from app.models.classroom import Cohort, CohortMember, CohortMemberRole, CohortStatus
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.payment import Payment
from app.models.user import User
from app.payments.base import CheckoutRequest as ProviderCheckoutRequest
from app.payments.base import WebhookEvent
from app.payments.factory import get_payment_provider
from app.schemas.payments import CheckoutResponse
from app.services.billing_accounts import BillingAccountService
from app.services.billing_obligations import PaymentObligationService
from app.services.billing_reconciliation import BillingReconciliationService
from app.services.email import EmailService
from app.services.tuition_plans import TuitionPlanService, to_major_int

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        email_service: EmailService,
    ) -> None:
        self.db = db
        self.settings = settings
        self.email_service = email_service

    def create_checkout(
        self,
        *,
        user: User,
        provider_name: PaymentProviderName,
        course_id: UUID | None = None,
        cohort_id: UUID | None = None,
        tuition_plan_id: UUID | None = None,
    ) -> CheckoutResponse:
        if cohort_id:
            return self._checkout_cohort(
                user=user,
                cohort_id=cohort_id,
                provider_name=provider_name,
                tuition_plan_id=tuition_plan_id,
            )
        if course_id:
            return self._checkout_course(user=user, course_id=course_id, provider_name=provider_name)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide course_id or cohort_id",
        )

    def create_obligation_checkout(
        self,
        *,
        user: User,
        obligation: PaymentObligation,
        provider_name: PaymentProviderName,
    ) -> CheckoutResponse:
        account = obligation.billing_account
        title = obligation.description or "Tuition installment"
        if account.cohort_id:
            cohort = self.db.get(Cohort, account.cohort_id)
            if cohort:
                title = f"{cohort.name} — {obligation.description}"
        return self._create_payment_session(
            user=user,
            provider_name=provider_name,
            amount=to_major_int(obligation.amount_due),
            currency=obligation.currency,
            title=title,
            course_id=account.course_id,
            cohort_id=account.cohort_id,
            billing_account_id=account.id,
            payment_obligation_id=obligation.id,
            metadata={
                "user_id": str(user.id),
                "cohort_id": str(account.cohort_id) if account.cohort_id else None,
                "course_id": str(account.course_id) if account.course_id else None,
                "billing_account_id": str(account.id),
                "payment_obligation_id": str(obligation.id),
                "kind": "tuition_obligation",
                "sequence_number": obligation.sequence_number,
            },
        )

    def _checkout_course(
        self,
        *,
        user: User,
        course_id: UUID,
        provider_name: PaymentProviderName,
    ) -> CheckoutResponse:
        course = self.db.get(Course, course_id)
        if not course or not course.published:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

        # Progressive launch: self-paced purchases gated until the video player is ready.
        live_slugs: set[str] = set()
        if course.slug not in live_slugs or course.price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This self-paced course is launching soon and is not open for enrollment yet",
            )

        existing = self.db.scalar(
            select(Enrollment).where(
                Enrollment.user_id == user.id,
                Enrollment.course_id == course.id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already enrolled in this course",
            )

        return self._create_payment_session(
            user=user,
            provider_name=provider_name,
            amount=course.price,
            currency=course.currency,
            title=course.title,
            course_id=course.id,
            cohort_id=None,
            metadata={
                "user_id": str(user.id),
                "course_id": str(course.id),
                "course_slug": course.slug,
                "kind": "course",
            },
        )

    def _checkout_cohort(
        self,
        *,
        user: User,
        cohort_id: UUID,
        provider_name: PaymentProviderName,
        tuition_plan_id: UUID | None = None,
    ) -> CheckoutResponse:
        cohort = self.db.get(Cohort, cohort_id)
        if not cohort:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")

        if cohort.status not in {CohortStatus.OPEN, CohortStatus.ACTIVE}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This cohort is not open for registration",
            )

        now = datetime.now(UTC)
        if cohort.registration_deadline and now > cohort.registration_deadline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration for this cohort has closed",
            )

        member = self.db.scalar(
            select(CohortMember).where(
                CohortMember.cohort_id == cohort.id,
                CohortMember.user_id == user.id,
            )
        )

        plans_enabled = self.settings.billing_plans_enabled
        available_plans = (
            TuitionPlanService(self.db).list_plans_for_cohort(cohort_id=cohort.id)
            if plans_enabled
            else []
        )

        if not member:
            # A returning payer with an unfinished payment resumes the same
            # checkout instead of minting a duplicate order/invoice.
            in_flight = self._find_in_flight_payment(
                user_id=user.id,
                provider_name=provider_name,
                cohort_id=cohort.id,
                course_id=None,
            )
            if in_flight is not None:
                logger.info(
                    "Reusing in-flight payment order=%s for cohort=%s user=%s",
                    in_flight.order_id,
                    cohort.id,
                    user.id,
                )
                return self._checkout_response_for_payment(in_flight)

        if plans_enabled and available_plans:
            if member:
                # Returning installment payers already have a seat.
                accounts = BillingAccountService(self.db)
                open_accounts = [
                    a
                    for a in accounts.list_for_student(user.id)
                    if a.cohort_id == cohort.id
                ]
                if not open_accounts:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="You are already registered for this cohort",
                    )
                account = accounts.get_account(open_accounts[0].id, student_id=user.id)
                payable = next(
                    (
                        o
                        for o in account.obligations
                        if o.status
                        in {
                            ObligationStatus.OPEN,
                            ObligationStatus.PAST_DUE,
                            ObligationStatus.PROCESSING,
                        }
                    ),
                    None,
                )
                if not payable:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No open tuition installment to pay",
                    )
                return self.create_obligation_checkout(
                    user=user, obligation=payable, provider_name=provider_name
                )

            if not tuition_plan_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Select a tuition plan to continue checkout",
                )
            if tuition_plan_id not in {p.id for p in available_plans}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tuition plan is not available for this cohort",
                )
            account = BillingAccountService(self.db).create_account(
                student=user,
                tuition_plan_id=tuition_plan_id,
                cohort_id=cohort.id,
                actor=user,
            )
            first = next(
                (o for o in account.obligations if o.sequence_number == 1),
                None,
            )
            if not first:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Billing account has no obligations",
                )
            first = PaymentObligationService(self.db).get_payable_obligation(
                first.id, student_id=user.id
            )
            return self.create_obligation_checkout(
                user=user, obligation=first, provider_name=provider_name
            )

        if member:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already registered for this cohort",
            )

        if cohort.price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This cohort is not priced for online checkout yet",
            )

        return self._create_payment_session(
            user=user,
            provider_name=provider_name,
            amount=cohort.price,
            currency=cohort.currency,
            title=cohort.name,
            course_id=cohort.course_id,
            cohort_id=cohort.id,
            metadata={
                "user_id": str(user.id),
                "cohort_id": str(cohort.id),
                "cohort_slug": cohort.slug,
                "course_id": str(cohort.course_id) if cohort.course_id else None,
                "kind": "cohort",
            },
        )

    def _create_payment_session(
        self,
        *,
        user: User,
        provider_name: PaymentProviderName,
        amount: int,
        currency: str,
        title: str,
        course_id: UUID | None,
        cohort_id: UUID | None,
        metadata: dict,
        billing_account_id: UUID | None = None,
        payment_obligation_id: UUID | None = None,
    ) -> CheckoutResponse:
        order_id = f"ord-{secrets.token_hex(12)}"
        provider = get_payment_provider(provider_name, self.settings)

        success_url = f"{self.settings.frontend_url}/checkout/success?order_id={order_id}"
        cancel_url = f"{self.settings.frontend_url}/checkout/cancel?order_id={order_id}"

        session = provider.create_checkout(
            ProviderCheckoutRequest(
                order_id=order_id,
                amount=amount,
                currency=currency,
                course_title=title,
                customer_email=user.email,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
            )
        )

        payment = Payment(
            order_id=order_id,
            user_id=user.id,
            course_id=course_id,
            cohort_id=cohort_id,
            billing_account_id=billing_account_id,
            payment_obligation_id=payment_obligation_id,
            provider=session.provider,
            provider_payment_id=session.provider_payment_id,
            amount=amount,
            currency=currency,
            crypto_currency=session.crypto_currency,
            crypto_amount=session.crypto_amount,
            status=PaymentStatus.PENDING,
            checkout_url=session.checkout_url,
            metadata_json={**(session.metadata or {}), **metadata},
        )
        self.db.add(payment)
        if payment_obligation_id:
            obligation = self.db.get(PaymentObligation, payment_obligation_id)
            if obligation and obligation.status in {
                ObligationStatus.OPEN,
                ObligationStatus.PAST_DUE,
            }:
                obligation.status = ObligationStatus.PROCESSING
        self.db.commit()
        self.db.refresh(payment)

        mode = "live" if self.settings.payment_mode == "live" else "mock"
        if provider_name == PaymentProviderName.PAYSTACK:
            mode = "live" if self.settings.paystack_secret_key else "mock"
        if provider_name == PaymentProviderName.NOWPAYMENTS:
            mode = "live" if self.settings.nowpayments_api_key else "mock"

        return CheckoutResponse(
            order_id=payment.order_id,
            provider=payment.provider,
            checkout_url=payment.checkout_url or "",
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            crypto_currency=payment.crypto_currency,
            crypto_amount=payment.crypto_amount,
            mode=mode,
            cohort_id=payment.cohort_id,
            course_id=payment.course_id,
        )

    def _find_in_flight_payment(
        self,
        *,
        user_id: UUID,
        provider_name: PaymentProviderName,
        course_id: UUID | None,
        cohort_id: UUID | None,
    ) -> Payment | None:
        """Most recent unfinished checkout for this item, so a returning payer
        resumes the original payment instead of creating a duplicate order."""
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        stmt = (
            select(Payment)
            .where(
                Payment.user_id == user_id,
                Payment.provider == provider_name,
                Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.CONFIRMING]),
                Payment.created_at >= cutoff,
                Payment.payment_obligation_id.is_(None),
                Payment.checkout_url.isnot(None),
            )
            .order_by(Payment.created_at.desc())
        )
        if cohort_id is not None:
            stmt = stmt.where(Payment.cohort_id == cohort_id)
        elif course_id is not None:
            stmt = stmt.where(Payment.course_id == course_id)
        else:
            return None
        return self.db.scalar(stmt)

    def _checkout_response_for_payment(self, payment: Payment) -> CheckoutResponse:
        mode = "live" if self.settings.payment_mode == "live" else "mock"
        if payment.provider == PaymentProviderName.PAYSTACK:
            mode = "live" if self.settings.paystack_secret_key else "mock"
        if payment.provider == PaymentProviderName.NOWPAYMENTS:
            mode = "live" if self.settings.nowpayments_api_key else "mock"
        return CheckoutResponse(
            order_id=payment.order_id,
            provider=payment.provider,
            checkout_url=payment.checkout_url or "",
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            crypto_currency=payment.crypto_currency,
            crypto_amount=payment.crypto_amount,
            mode=mode,
            cohort_id=payment.cohort_id,
            course_id=payment.course_id,
        )

    def get_payment_for_user(self, *, user: User, order_id: str) -> Payment:
        payment = self.db.scalar(select(Payment).where(Payment.order_id == order_id))
        if not payment or payment.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        self._maybe_auto_reconcile(payment)
        self.db.refresh(payment)
        return payment

    def _maybe_auto_reconcile(self, payment: Payment) -> None:
        """Pull the real status from NOWPayments when a live payment is stuck
        pending/confirming, so a missed IPN self-heals the next time anyone
        (success page poll, admin) reads the payment. Throttled to one lookup
        per minute per order."""
        if payment.provider != PaymentProviderName.NOWPAYMENTS:
            return
        if payment.status not in {PaymentStatus.PENDING, PaymentStatus.CONFIRMING}:
            return
        if not self.settings.nowpayments_api_key:
            return
        created = payment.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        if (datetime.now(UTC) - created).total_seconds() < 90:
            return  # give the IPN a chance to arrive first
        meta = dict(payment.metadata_json or {})
        last = meta.get("last_auto_reconcile_at")
        now = datetime.now(UTC)
        if last:
            try:
                if (now - datetime.fromisoformat(last)).total_seconds() < 60:
                    return
            except (ValueError, TypeError):
                pass
        meta["last_auto_reconcile_at"] = now.isoformat()
        payment.metadata_json = meta
        self.db.commit()
        try:
            self._reconcile_nowpayments_payment(payment, payment_id=None)
        except HTTPException as exc:
            logger.info("Auto-reconcile for order=%s: %s", payment.order_id, exc.detail)

    def reconcile_payment(self, *, order_id: str, payment_id: str | None = None) -> Payment:
        """Admin fallback for missed/failed webhooks: pull the live status straight from the provider."""
        payment = self.db.scalar(select(Payment).where(Payment.order_id == order_id))
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

        if payment.provider == PaymentProviderName.NOWPAYMENTS:
            return self._reconcile_nowpayments_payment(payment, payment_id=payment_id)
        if payment.provider == PaymentProviderName.PAYSTACK:
            return self._reconcile_paystack_payment(payment)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reconciliation is not supported for this provider",
        )

    def reconcile_stale_nowpayments(
        self,
        *,
        older_than_seconds: int = 120,
        limit: int = 25,
    ) -> dict[str, int]:
        """Sweep stale NOWPayments payments and pull their real status.

        Safety net for missed or late IPNs. The success page can only poll while
        it is open, so a payment that settles after the payer closed the tab (or
        after the ~10 minute poll window) would otherwise sit at ``pending`` until
        an admin reconciles it by hand. This runs the same idempotent pipeline as
        the webhook (dedupe table prevents a double confirmation) and unlocks the
        seat once the provider reports the payment as ``finished``.
        """
        summary = {"scanned": 0, "confirmed": 0, "updated": 0, "failed": 0}
        if not self.settings.nowpayments_api_key:
            return summary

        cutoff = datetime.now(UTC) - timedelta(seconds=max(older_than_seconds, 0))
        stale = list(
            self.db.scalars(
                select(Payment)
                .where(
                    Payment.provider == PaymentProviderName.NOWPAYMENTS,
                    Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.CONFIRMING]),
                    Payment.created_at < cutoff,
                )
                .order_by(Payment.created_at.asc())
                .limit(max(limit, 1))
            ).all()
        )

        for payment in stale:
            summary["scanned"] += 1
            before = payment.status
            try:
                updated = self._reconcile_nowpayments_payment(payment, payment_id=None)
            except HTTPException as exc:
                # A 404 simply means the customer never sent funds yet — not an
                # error worth escalating every sweep.
                if exc.status_code != status.HTTP_404_NOT_FOUND:
                    summary["failed"] += 1
                    logger.warning(
                        "Payments sweep failed order=%s status=%s detail=%s",
                        payment.order_id,
                        exc.status_code,
                        exc.detail,
                    )
                continue
            except Exception:
                summary["failed"] += 1
                logger.exception("Payments sweep crashed order=%s", payment.order_id)
                self.db.rollback()
                continue

            if updated.status == PaymentStatus.CONFIRMED and before != PaymentStatus.CONFIRMED:
                summary["confirmed"] += 1
            elif updated.status != before:
                summary["updated"] += 1

        if summary["confirmed"] or summary["updated"] or summary["failed"]:
            logger.info("Payments reconcile sweep %s", summary)
        return summary

    def _reconcile_nowpayments_payment(self, payment: Payment, *, payment_id: str | None) -> Payment:
        """Pull the live record from NOWPayments and feed it through the normal
        webhook pipeline. With no payment_id supplied, the record is discovered
        automatically by our order_id via the payments list endpoint."""
        from app.payments.nowpayments_provider import NOWPaymentsProvider, map_nowpayments_status

        provider = get_payment_provider(PaymentProviderName.NOWPAYMENTS, self.settings)
        if not isinstance(provider, NOWPaymentsProvider) or not provider.is_live:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="NOWPayments live mode is not configured",
            )

        if payment_id:
            record = provider.fetch_payment_by_id(payment_id)
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No NOWPayments payment found with that payment ID",
                )
        else:
            record = None
            meta = dict(payment.metadata_json or {})
            # Fast path: an earlier lookup already resolved the real payment id.
            known_payment_id = str(meta.get("nowpayments_payment_id") or "").strip()
            if known_payment_id:
                try:
                    record = provider.fetch_payment_by_id(known_payment_id)
                except HTTPException:
                    record = None
            if not record:
                record = provider.find_payment_for_order(payment.order_id)
            if not record:
                invoice_id = str(meta.get("invoice_id") or "").strip()
                if invoice_id:
                    record = provider.find_payment_by_invoice(invoice_id)
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        "No NOWPayments payment found for this order yet — the customer "
                        "may not have sent funds"
                    ),
                )
        # Invoice payments do not always echo our order_id. Only reject a record
        # when it clearly belongs to a *different* order we set.
        record_order = str(record.get("order_id") or "").strip()
        if record_order and record_order != payment.order_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That payment ID belongs to a different order",
            )

        resolved_payment_id = str(record.get("payment_id") or "").strip()
        if resolved_payment_id:
            # Remember it so later reconciles skip the list scan.
            payment.metadata_json = {
                **(payment.metadata_json or {}),
                "nowpayments_payment_id": resolved_payment_id,
            }

        event = WebhookEvent(
            provider=PaymentProviderName.NOWPAYMENTS,
            order_id=payment.order_id,
            provider_payment_id=str(
                record.get("payment_id") or record.get("invoice_id") or payment.order_id
            ),
            status=map_nowpayments_status(str(record.get("payment_status") or "")),
            crypto_currency=record.get("pay_currency"),
            crypto_amount=(
                str(record["pay_amount"]) if record.get("pay_amount") is not None else None
            ),
            raw={**record, "reconciled_by_admin": True},
        )
        return self.process_webhook_event(event)

    def _reconcile_paystack_payment(self, payment: Payment) -> Payment:
        """No admin input needed: Paystack verify is keyed by our own stored reference."""
        from app.payments.paystack_provider import PaystackProvider

        provider = get_payment_provider(PaymentProviderName.PAYSTACK, self.settings)
        if not isinstance(provider, PaystackProvider) or not provider.is_live:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Paystack live mode is not configured",
            )
        if not payment.provider_payment_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Paystack reference stored for this order",
            )

        verified = provider.fetch_verified_transaction(payment.provider_payment_id)
        paystack_status = str(verified.get("status") or "").lower()
        event = WebhookEvent(
            provider=PaymentProviderName.PAYSTACK,
            order_id=payment.order_id,
            provider_payment_id=str(verified.get("id") or payment.provider_payment_id),
            status=provider.map_status(event="charge.success", paystack_status=paystack_status),
            crypto_currency=None,
            crypto_amount=None,
            raw={"verified": verified, "reconciled_by_admin": True},
        )
        return self.process_webhook_event(event)

    def process_webhook_event(self, event: WebhookEvent) -> Payment:
        payment = self.db.scalar(select(Payment).where(Payment.order_id == event.order_id))
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

        reconciliation = BillingReconciliationService(self.db)
        event_key = (
            f"{event.order_id}:{event.status.value}:"
            f"{event.provider_payment_id or payment.provider_payment_id or 'none'}"
        )
        is_new = reconciliation.record_webhook_event(
            provider=event.provider.value,
            event_key=event_key,
            payment_id=payment.id,
            payload=event.raw if isinstance(event.raw, dict) else None,
        )
        if not is_new:
            self.db.commit()
            self.db.refresh(payment)
            return payment

        if payment.provider != event.provider and event.provider != PaymentProviderName.MOCK:
            if not (
                not self.settings.is_production
                and event.provider
                in {
                    PaymentProviderName.PAYSTACK,
                    PaymentProviderName.NOWPAYMENTS,
                }
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Provider mismatch for this order",
                )

        if payment.status == PaymentStatus.CONFIRMED:
            if event.status == PaymentStatus.REFUNDED:
                payment.status = PaymentStatus.REFUNDED
                payment.metadata_json = {
                    **(payment.metadata_json or {}),
                    "last_webhook": event.raw,
                }
                from app.services.referrals import ReferralCommissionService

                ReferralCommissionService(self.db, self.settings).handle_refunded_payment(payment)
                self.db.commit()
                self.db.refresh(payment)
                return payment
            self.db.commit()
            return payment

        if event.provider_payment_id:
            payment.provider_payment_id = event.provider_payment_id
        if event.crypto_currency:
            payment.crypto_currency = event.crypto_currency
        if event.crypto_amount:
            payment.crypto_amount = event.crypto_amount

        payment.status = event.status
        payment.metadata_json = {
            **(payment.metadata_json or {}),
            "last_webhook": event.raw,
        }

        if event.status == PaymentStatus.CONFIRMED:
            if payment.provider == PaymentProviderName.NOWPAYMENTS:
                from app.payments.nowpayments_provider import amounts_match

                reported = (event.raw or {}).get("price_amount")
                if not amounts_match(expected=payment.amount, reported=reported):
                    logger.error(
                        "NOWPayments amount mismatch order=%s expected=%s reported=%s",
                        payment.order_id,
                        payment.amount,
                        reported,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Payment amount mismatch",
                    )

            if payment.provider == PaymentProviderName.PAYSTACK:
                from app.payments.paystack_provider import from_paystack_subunit

                verified = (event.raw or {}).get("verified") or {}
                meta = payment.metadata_json or {}
                expected_currency = str(
                    meta.get("charge_currency") or payment.currency or ""
                ).upper()
                expected_major = meta.get("charge_amount")
                if expected_major is None:
                    expected_major = payment.amount

                reported_subunit = verified.get("amount")
                reported_currency = str(verified.get("currency") or "").upper()
                if reported_currency and expected_currency and reported_currency != expected_currency:
                    logger.error(
                        "Paystack currency mismatch order=%s expected=%s reported=%s",
                        payment.order_id,
                        expected_currency,
                        reported_currency,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Payment currency mismatch",
                    )
                if reported_subunit is not None:
                    reported_major = from_paystack_subunit(
                        reported_subunit, reported_currency or expected_currency
                    )
                    if abs(float(expected_major) - float(reported_major)) > 0.01:
                        logger.error(
                            "Paystack amount mismatch order=%s expected=%s reported=%s",
                            payment.order_id,
                            expected_major,
                            reported_major,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Payment amount mismatch",
                        )

            payment.confirmed_at = datetime.now(UTC)
            billing_account = reconciliation.reconcile_confirmed_payment(payment)

            enrollment = None
            if payment.course_id and not payment.payment_obligation_id:
                enrollment = self._unlock_enrollment(payment)
            if payment.cohort_id:
                should_unlock = True
                if billing_account is not None:
                    should_unlock = reconciliation.first_obligation_paid(billing_account)
                if should_unlock:
                    self._unlock_cohort_membership(payment)

            from app.services.referrals import ReferralCommissionService

            ReferralCommissionService(self.db, self.settings).handle_successful_payment(payment)

            self.db.commit()
            self.db.refresh(payment)

            user = self.db.get(User, payment.user_id)
            title = self._payment_title(payment)
            if user:
                self.email_service.send_payment_receipt(
                    email=user.email,
                    course_title=title,
                    amount=payment.amount,
                    currency=payment.currency,
                    order_id=payment.order_id,
                    provider=payment.provider.value,
                )
                if payment.course_id and enrollment is not None:
                    course = self.db.get(Course, payment.course_id)
                    if course:
                        self.email_service.send_enrollment_confirmation(
                            email=user.email,
                            course_title=course.title,
                            course_slug=course.slug,
                        )
                elif payment.cohort_id and (
                    billing_account is None
                    or reconciliation.first_obligation_paid(billing_account)
                ):
                    cohort = self.db.get(Cohort, payment.cohort_id)
                    if cohort:
                        self.email_service.send_enrollment_confirmation(
                            email=user.email,
                            course_title=cohort.name,
                            course_slug=cohort.slug,
                            access_path="/classroom",
                        )
            logger.info(
                "Payment confirmed order=%s enrollment=%s cohort=%s obligation=%s",
                payment.order_id,
                enrollment.id if enrollment else None,
                payment.cohort_id,
                payment.payment_obligation_id,
            )
            return payment

        if event.status in {PaymentStatus.FAILED, PaymentStatus.EXPIRED}:
            if payment.payment_obligation_id:
                obligation = self.db.get(PaymentObligation, payment.payment_obligation_id)
                if obligation and obligation.status == ObligationStatus.PROCESSING:
                    obligation.status = ObligationStatus.OPEN

        if event.status == PaymentStatus.REFUNDED:
            from app.services.referrals import ReferralCommissionService

            ReferralCommissionService(self.db, self.settings).handle_refunded_payment(payment)

        self.db.commit()
        self.db.refresh(payment)
        return payment

    def _payment_title(self, payment: Payment) -> str:
        if payment.cohort_id:
            cohort = self.db.get(Cohort, payment.cohort_id)
            if cohort:
                return cohort.name
        if payment.course_id:
            course = self.db.get(Course, payment.course_id)
            if course:
                return course.title
        return "Analytic Sages enrollment"

    def _unlock_enrollment(self, payment: Payment) -> Enrollment:
        assert payment.course_id is not None
        existing = self.db.scalar(
            select(Enrollment).where(
                Enrollment.user_id == payment.user_id,
                Enrollment.course_id == payment.course_id,
            )
        )
        if existing:
            existing.status = EnrollmentStatus.ACTIVE
            existing.payment_id = payment.id
            existing.enrolled_at = datetime.now(UTC)
            return existing

        enrollment = Enrollment(
            user_id=payment.user_id,
            course_id=payment.course_id,
            payment_id=payment.id,
            status=EnrollmentStatus.ACTIVE,
        )
        self.db.add(enrollment)
        self.db.flush()
        return enrollment

    def _unlock_cohort_membership(self, payment: Payment) -> CohortMember:
        assert payment.cohort_id is not None
        existing = self.db.scalar(
            select(CohortMember).where(
                CohortMember.cohort_id == payment.cohort_id,
                CohortMember.user_id == payment.user_id,
            )
        )
        if existing:
            return existing

        member = CohortMember(
            cohort_id=payment.cohort_id,
            user_id=payment.user_id,
            role=CohortMemberRole.STUDENT,
        )
        self.db.add(member)
        self.db.flush()
        return member
