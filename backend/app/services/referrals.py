"""Referral Partner services: onboarding, attribution, commission, ledger, payouts."""

from __future__ import annotations

import hashlib
import logging
import secrets
import string
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.payments import PaymentStatus
from app.core.referrals import (
    PartnerLedgerEntryType,
    PartnerLedgerStatus,
    PartnerPayoutStatus,
    ReferralConversionStatus,
    ReferralPartnerStatus,
    commission_from_payment_amount,
    referral_money,
)
from app.models.classroom import Cohort
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.payment import Payment
from app.models.referral import (
    PartnerLedgerEntry,
    PartnerPayoutRequest,
    ReferralAttribution,
    ReferralAuditEvent,
    ReferralClick,
    ReferralConversion,
    ReferralPartner,
)
from app.models.user import User

logger = logging.getLogger(__name__)

VISITOR_COOKIE = "as_ref_vid"
CODE_ALPHABET = string.ascii_uppercase + string.digits


def hash_privacy_value(value: str | None, *, secret: str) -> str | None:
    if not value:
        return None
    digest = hashlib.sha256(f"{secret}:{value}".encode()).hexdigest()
    return digest[:64]


def generate_referral_code(*, length: int = 8) -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(length))


class ReferralPartnerService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def get_by_user(self, user_id: UUID) -> ReferralPartner | None:
        return self.db.scalar(select(ReferralPartner).where(ReferralPartner.user_id == user_id))

    def get_active_by_code(self, code: str) -> ReferralPartner | None:
        normalized = code.strip().upper()
        partner = self.db.scalar(
            select(ReferralPartner).where(ReferralPartner.referral_code == normalized)
        )
        if not partner or partner.status != ReferralPartnerStatus.ACTIVE:
            return None
        return partner

    def apply(
        self,
        *,
        user: User,
        display_name: str,
        social_handle: str | None,
        promotion_channels: str | None,
        terms_accepted: bool,
    ) -> ReferralPartner:
        if not terms_accepted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must accept the Referral Partner terms",
            )
        existing = self.get_by_user(user.id)
        if existing:
            if existing.status == ReferralPartnerStatus.REJECTED:
                existing.status = ReferralPartnerStatus.PENDING
                existing.display_name = display_name.strip() or (user.full_name or user.email)
                existing.social_handle = social_handle
                existing.promotion_channels = promotion_channels
                existing.terms_accepted_at = datetime.now(UTC)
                existing.admin_note = None
                self._audit(
                    actor_id=user.id,
                    action="partner.reapply",
                    entity_id=existing.id,
                    after={"status": existing.status.value},
                )
                self.db.commit()
                self.db.refresh(existing)
                return existing
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a Referral Partner application",
            )

        partner = ReferralPartner(
            user_id=user.id,
            status=ReferralPartnerStatus.PENDING,
            display_name=display_name.strip() or (user.full_name or user.email.split("@")[0]),
            social_handle=social_handle,
            promotion_channels=promotion_channels,
            terms_accepted_at=datetime.now(UTC),
        )
        self.db.add(partner)
        self.db.flush()
        self._audit(
            actor_id=user.id,
            action="partner.apply",
            entity_id=partner.id,
            after={"status": partner.status.value},
        )
        self.db.commit()
        self.db.refresh(partner)
        return partner

    def set_status(
        self,
        *,
        partner_id: UUID,
        status_value: ReferralPartnerStatus,
        actor: User,
        note: str | None = None,
        regenerate_code: bool = False,
    ) -> ReferralPartner:
        partner = self.db.get(ReferralPartner, partner_id)
        if not partner:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")

        before = {"status": partner.status.value, "referral_code": partner.referral_code}
        partner.status = status_value
        if note is not None:
            partner.admin_note = note

        if status_value == ReferralPartnerStatus.ACTIVE:
            partner.approved_at = datetime.now(UTC)
            partner.approved_by = actor.id
            if not partner.referral_code or regenerate_code:
                partner.referral_code = self._unique_code()

        self._audit(
            actor_id=actor.id,
            action=f"partner.{status_value.value}",
            entity_id=partner.id,
            note=note,
            before=before,
            after={"status": partner.status.value, "referral_code": partner.referral_code},
        )
        self.db.commit()
        self.db.refresh(partner)
        return partner

    def regenerate_code(self, *, partner_id: UUID, actor: User) -> ReferralPartner:
        partner = self.db.get(ReferralPartner, partner_id)
        if not partner:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")
        before = partner.referral_code
        partner.referral_code = self._unique_code()
        self._audit(
            actor_id=actor.id,
            action="partner.regenerate_code",
            entity_id=partner.id,
            before={"referral_code": before},
            after={"referral_code": partner.referral_code},
        )
        self.db.commit()
        self.db.refresh(partner)
        return partner

    def list_partners(
        self,
        *,
        status_filter: ReferralPartnerStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReferralPartner]:
        stmt: Select[tuple[ReferralPartner]] = select(ReferralPartner).order_by(
            ReferralPartner.created_at.desc()
        )
        if status_filter:
            stmt = stmt.where(ReferralPartner.status == status_filter)
        return list(self.db.scalars(stmt.limit(limit).offset(offset)).all())

    def _unique_code(self) -> str:
        for _ in range(20):
            code = generate_referral_code()
            exists = self.db.scalar(
                select(ReferralPartner.id).where(ReferralPartner.referral_code == code)
            )
            if not exists:
                return code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate referral code",
        )

    def _audit(
        self,
        *,
        actor_id: UUID | None,
        action: str,
        entity_id: UUID | None,
        note: str | None = None,
        before: dict | None = None,
        after: dict | None = None,
    ) -> None:
        self.db.add(
            ReferralAuditEvent(
                actor_id=actor_id,
                action=action,
                entity_type="referral_partner",
                entity_id=entity_id,
                note=note,
                before_json=before,
                after_json=after,
            )
        )


class ReferralAttributionService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.partners = ReferralPartnerService(db, settings)

    def track_click(
        self,
        *,
        code: str,
        anonymous_visitor_id: str,
        landing_path: str | None,
        ip: str | None,
        user_agent: str | None,
        destination: str | None = None,
    ) -> tuple[bool, str]:
        """Record click + first-touch attribution. Returns (ok, redirect_path)."""
        redirect = destination or self.settings.referral_default_redirect_path
        if not redirect.startswith("/"):
            redirect = self.settings.referral_default_redirect_path

        partner = self.partners.get_active_by_code(code)
        if not partner or not partner.referral_code:
            return False, redirect

        secret = self.settings.secret_key
        self.db.add(
            ReferralClick(
                partner_id=partner.id,
                referral_code=partner.referral_code,
                anonymous_visitor_id=anonymous_visitor_id,
                landing_path=landing_path,
                ip_hash=hash_privacy_value(ip, secret=secret),
                user_agent_hash=hash_privacy_value(user_agent, secret=secret),
            )
        )

        now = datetime.now(UTC)
        existing = self.db.scalar(
            select(ReferralAttribution)
            .where(ReferralAttribution.anonymous_visitor_id == anonymous_visitor_id)
            .order_by(ReferralAttribution.attributed_at.desc())
        )
        # First valid referral wins — do not overwrite unexpired attribution
        if existing and existing.expires_at > now and existing.locked_at is None:
            self.db.commit()
            return True, redirect

        if existing and existing.locked_at is not None:
            self.db.commit()
            return True, redirect

        self.db.add(
            ReferralAttribution(
                partner_id=partner.id,
                anonymous_visitor_id=anonymous_visitor_id,
                referral_code=partner.referral_code,
                landing_path=landing_path,
                attributed_at=now,
                expires_at=now + timedelta(days=self.settings.referral_attribution_days),
            )
        )
        self.db.commit()
        return True, redirect

    def lock_for_new_user(self, *, user: User, anonymous_visitor_id: str | None) -> None:
        """Associate and lock attribution when a genuinely new user registers."""
        if not anonymous_visitor_id:
            return

        # Existing locked attribution for this user → never replace
        locked = self.db.scalar(
            select(ReferralAttribution).where(
                ReferralAttribution.referred_user_id == user.id,
                ReferralAttribution.locked_at.is_not(None),
            )
        )
        if locked:
            return

        now = datetime.now(UTC)
        attr = self.db.scalar(
            select(ReferralAttribution)
            .where(
                ReferralAttribution.anonymous_visitor_id == anonymous_visitor_id,
                ReferralAttribution.locked_at.is_(None),
                ReferralAttribution.expires_at > now,
            )
            .order_by(ReferralAttribution.attributed_at.asc())
        )
        if not attr:
            return

        partner = self.db.get(ReferralPartner, attr.partner_id)
        if not partner or partner.status != ReferralPartnerStatus.ACTIVE:
            return
        if partner.user_id == user.id:
            # Self-referral — do not lock
            return

        attr.referred_user_id = user.id
        attr.locked_at = now
        self.db.add(
            ReferralAuditEvent(
                actor_id=user.id,
                action="attribution.locked",
                entity_type="referral_attribution",
                entity_id=attr.id,
                after_json={"referred_user_id": str(user.id), "partner_id": str(partner.id)},
            )
        )
        # Caller commits with user creation transaction when possible

    def get_locked_for_user(self, user_id: UUID) -> ReferralAttribution | None:
        return self.db.scalar(
            select(ReferralAttribution).where(
                ReferralAttribution.referred_user_id == user_id,
                ReferralAttribution.locked_at.is_not(None),
            )
        )


class ReferralCommissionService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.attribution = ReferralAttributionService(db, settings)

    @property
    def default_rate(self) -> Decimal:
        return Decimal(self.settings.default_referral_commission_rate)

    def handle_successful_payment(self, payment: Payment) -> ReferralConversion | None:
        """Idempotent payment-level commission creation. Safe for duplicate calls."""
        if payment.status != PaymentStatus.CONFIRMED:
            return None

        existing = self.db.scalar(
            select(ReferralConversion).where(ReferralConversion.payment_id == payment.id)
        )
        if existing:
            return existing

        if payment.amount <= 0:
            return None

        attr = self.attribution.get_locked_for_user(payment.user_id)
        if not attr:
            return None

        partner = self.db.get(ReferralPartner, attr.partner_id)
        if not partner or partner.status != ReferralPartnerStatus.ACTIVE:
            return None
        if partner.user_id == payment.user_id:
            return None

        if not self._is_eligible(payment):
            return None

        rate = self.default_rate
        eligible = referral_money(payment.amount)
        commission = commission_from_payment_amount(eligible_amount=eligible, rate=rate)
        if commission <= 0:
            return None

        available_at = datetime.now(UTC) + timedelta(days=self.settings.commission_hold_days)
        enrollment_id = None
        if payment.course_id:
            enrollment = self.db.scalar(
                select(Enrollment).where(
                    Enrollment.user_id == payment.user_id,
                    Enrollment.course_id == payment.course_id,
                )
            )
            if enrollment:
                enrollment_id = enrollment.id

        conversion = ReferralConversion(
            partner_id=partner.id,
            referred_user_id=payment.user_id,
            course_id=payment.course_id,
            cohort_id=payment.cohort_id,
            enrollment_id=enrollment_id,
            payment_id=payment.id,
            payment_obligation_id=payment.payment_obligation_id,
            eligible_amount=eligible,
            commission_rate=rate,
            commission_amount=commission,
            currency=payment.currency.upper(),
            status=ReferralConversionStatus.PENDING,
            available_at=available_at,
        )
        self.db.add(conversion)
        self.db.flush()

        ledger = PartnerLedgerEntry(
            partner_id=partner.id,
            entry_type=PartnerLedgerEntryType.COMMISSION,
            amount=commission,
            currency=payment.currency.upper(),
            reference_type="referral_conversion",
            reference_id=conversion.id,
            status=PartnerLedgerStatus.PENDING,
            description="Referral commission (holding period)",
            available_at=available_at,
        )
        self.db.add(ledger)
        logger.info(
            "referral_commission payment=%s partner=%s amount=%s %s",
            payment.id,
            partner.id,
            commission,
            payment.currency,
        )
        return conversion

    def handle_refunded_payment(self, payment: Payment) -> None:
        conversion = self.db.scalar(
            select(ReferralConversion).where(ReferralConversion.payment_id == payment.id)
        )
        if not conversion:
            return

        if conversion.status == ReferralConversionStatus.VOIDED:
            return
        if conversion.status == ReferralConversionStatus.REVERSED:
            return

        if conversion.status == ReferralConversionStatus.PENDING:
            conversion.status = ReferralConversionStatus.VOIDED
            entry = self.db.scalar(
                select(PartnerLedgerEntry).where(
                    PartnerLedgerEntry.partner_id == conversion.partner_id,
                    PartnerLedgerEntry.entry_type == PartnerLedgerEntryType.COMMISSION,
                    PartnerLedgerEntry.reference_type == "referral_conversion",
                    PartnerLedgerEntry.reference_id == conversion.id,
                )
            )
            if entry and entry.status != PartnerLedgerStatus.VOIDED:
                entry.status = PartnerLedgerStatus.VOIDED
            self.db.add(
                ReferralAuditEvent(
                    action="conversion.voided",
                    entity_type="referral_conversion",
                    entity_id=conversion.id,
                    after_json={"reason": "payment_refunded"},
                )
            )
            return

        if conversion.status == ReferralConversionStatus.AVAILABLE:
            conversion.status = ReferralConversionStatus.REVERSED
            self.db.add(
                PartnerLedgerEntry(
                    partner_id=conversion.partner_id,
                    entry_type=PartnerLedgerEntryType.REVERSAL,
                    amount=referral_money(-conversion.commission_amount),
                    currency=conversion.currency,
                    reference_type="referral_conversion",
                    reference_id=conversion.id,
                    status=PartnerLedgerStatus.COMPLETED,
                    description="Commission reversal after refund",
                )
            )
            self.db.add(
                ReferralAuditEvent(
                    action="conversion.reversed",
                    entity_type="referral_conversion",
                    entity_id=conversion.id,
                    after_json={"reason": "payment_refunded"},
                )
            )
            return

        # Already paid out path — flag for admin
        conversion.status = ReferralConversionStatus.REVIEW_REQUIRED
        self.db.add(
            ReferralAuditEvent(
                action="conversion.review_required",
                entity_type="referral_conversion",
                entity_id=conversion.id,
                after_json={"reason": "refund_after_payout_or_reserved"},
            )
        )

    def release_held_commissions(self, *, now: datetime | None = None) -> int:
        """Move pending commissions past hold period to available. Idempotent."""
        now = now or datetime.now(UTC)
        conversions = list(
            self.db.scalars(
                select(ReferralConversion).where(
                    ReferralConversion.status == ReferralConversionStatus.PENDING,
                    ReferralConversion.available_at.is_not(None),
                    ReferralConversion.available_at <= now,
                )
            ).all()
        )
        released = 0
        for conversion in conversions:
            conversion.status = ReferralConversionStatus.AVAILABLE
            entry = self.db.scalar(
                select(PartnerLedgerEntry).where(
                    PartnerLedgerEntry.partner_id == conversion.partner_id,
                    PartnerLedgerEntry.entry_type == PartnerLedgerEntryType.COMMISSION,
                    PartnerLedgerEntry.reference_type == "referral_conversion",
                    PartnerLedgerEntry.reference_id == conversion.id,
                    PartnerLedgerEntry.status == PartnerLedgerStatus.PENDING,
                )
            )
            if entry:
                entry.status = PartnerLedgerStatus.AVAILABLE
            released += 1
        if released:
            self.db.commit()
        return released

    def _is_eligible(self, payment: Payment) -> bool:
        if payment.course_id:
            course = self.db.get(Course, payment.course_id)
            if course:
                if course.is_free:
                    return False
                if not course.referral_commission_eligible:
                    return False
        if payment.cohort_id:
            cohort = self.db.get(Cohort, payment.cohort_id)
            if cohort and not cohort.referral_commission_eligible:
                return False
        # Must be tied to a paid programme (course or cohort)
        if not payment.course_id and not payment.cohort_id:
            return False
        return True


class ReferralLedgerService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def available_balance(self, *, partner_id: UUID, currency: str) -> Decimal:
        currency = currency.upper()
        # Positive AVAILABLE commissions/adjustments
        credits = self.db.scalar(
            select(func.coalesce(func.sum(PartnerLedgerEntry.amount), 0)).where(
                PartnerLedgerEntry.partner_id == partner_id,
                PartnerLedgerEntry.currency == currency,
                PartnerLedgerEntry.status == PartnerLedgerStatus.AVAILABLE,
                PartnerLedgerEntry.entry_type.in_(
                    [PartnerLedgerEntryType.COMMISSION, PartnerLedgerEntryType.ADJUSTMENT]
                ),
            )
        )
        # Completed reversals (negative) reduce available
        reversals = self.db.scalar(
            select(func.coalesce(func.sum(PartnerLedgerEntry.amount), 0)).where(
                PartnerLedgerEntry.partner_id == partner_id,
                PartnerLedgerEntry.currency == currency,
                PartnerLedgerEntry.entry_type == PartnerLedgerEntryType.REVERSAL,
                PartnerLedgerEntry.status == PartnerLedgerStatus.COMPLETED,
            )
        )
        # Reserved / processing / completed payouts (negative amounts)
        payouts = self.db.scalar(
            select(func.coalesce(func.sum(PartnerLedgerEntry.amount), 0)).where(
                PartnerLedgerEntry.partner_id == partner_id,
                PartnerLedgerEntry.currency == currency,
                PartnerLedgerEntry.entry_type == PartnerLedgerEntryType.PAYOUT,
                PartnerLedgerEntry.status.in_(
                    [
                        PartnerLedgerStatus.RESERVED,
                        PartnerLedgerStatus.PROCESSING,
                        PartnerLedgerStatus.COMPLETED,
                    ]
                ),
            )
        )
        total = (
            referral_money(credits)
            + referral_money(reversals)
            + referral_money(payouts)
        )
        return referral_money(total)

    def pending_commission(self, *, partner_id: UUID, currency: str | None = None) -> Decimal:
        stmt = select(func.coalesce(func.sum(PartnerLedgerEntry.amount), 0)).where(
            PartnerLedgerEntry.partner_id == partner_id,
            PartnerLedgerEntry.status == PartnerLedgerStatus.PENDING,
            PartnerLedgerEntry.entry_type == PartnerLedgerEntryType.COMMISSION,
        )
        if currency:
            stmt = stmt.where(PartnerLedgerEntry.currency == currency.upper())
        return referral_money(self.db.scalar(stmt) or 0)

    def total_paid_out(self, *, partner_id: UUID, currency: str | None = None) -> Decimal:
        stmt = select(func.coalesce(func.sum(PartnerLedgerEntry.amount), 0)).where(
            PartnerLedgerEntry.partner_id == partner_id,
            PartnerLedgerEntry.entry_type == PartnerLedgerEntryType.PAYOUT,
            PartnerLedgerEntry.status == PartnerLedgerStatus.COMPLETED,
        )
        if currency:
            stmt = stmt.where(PartnerLedgerEntry.currency == currency.upper())
        # amounts are negative
        return referral_money(abs(Decimal(str(self.db.scalar(stmt) or 0))))


class ReferralPayoutService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.ledger = ReferralLedgerService(db)

    @property
    def minimum_amount(self) -> Decimal:
        return referral_money(self.settings.minimum_payout_amount)

    @property
    def minimum_currency(self) -> str:
        return self.settings.minimum_payout_currency.upper()

    def request_payout(
        self,
        *,
        partner: ReferralPartner,
        amount: Decimal,
        currency: str,
        payment_details_reference: str | None = None,
    ) -> PartnerPayoutRequest:
        if partner.status != ReferralPartnerStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only active partners can request payouts",
            )
        currency = currency.upper()
        amount = referral_money(amount)
        if currency != self.minimum_currency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payouts are currently only supported in {self.minimum_currency}",
            )
        if amount < self.minimum_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Minimum payout is {self.minimum_amount} {currency}",
            )

        # Lock partner row for concurrent request protection
        locked = self.db.scalar(
            select(ReferralPartner)
            .where(ReferralPartner.id == partner.id)
            .with_for_update()
        )
        if not locked:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")

        available = self.ledger.available_balance(partner_id=partner.id, currency=currency)
        if amount > available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requested amount exceeds available balance",
            )

        open_request = self.db.scalar(
            select(PartnerPayoutRequest).where(
                PartnerPayoutRequest.partner_id == partner.id,
                PartnerPayoutRequest.status.in_(
                    [
                        PartnerPayoutStatus.REQUESTED,
                        PartnerPayoutStatus.APPROVED,
                        PartnerPayoutStatus.PROCESSING,
                    ]
                ),
            )
        )
        if open_request:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have an open payout request",
            )

        payout = PartnerPayoutRequest(
            partner_id=partner.id,
            amount=amount,
            currency=currency,
            payment_method="manual",
            payment_details_reference=payment_details_reference,
            status=PartnerPayoutStatus.REQUESTED,
        )
        self.db.add(payout)
        self.db.flush()

        # Reserve funds (negative amount)
        self.db.add(
            PartnerLedgerEntry(
                partner_id=partner.id,
                entry_type=PartnerLedgerEntryType.PAYOUT,
                amount=referral_money(-amount),
                currency=currency,
                reference_type="partner_payout_request",
                reference_id=payout.id,
                status=PartnerLedgerStatus.RESERVED,
                description="Payout request reserved",
            )
        )
        self.db.add(
            ReferralAuditEvent(
                actor_id=partner.user_id,
                action="payout.requested",
                entity_type="partner_payout_request",
                entity_id=payout.id,
                after_json={"amount": str(amount), "currency": currency},
            )
        )
        self.db.commit()
        self.db.refresh(payout)
        return payout

    def update_status(
        self,
        *,
        payout_id: UUID,
        status_value: PartnerPayoutStatus,
        actor: User,
        note: str | None = None,
    ) -> PartnerPayoutRequest:
        payout = self.db.scalar(
            select(PartnerPayoutRequest)
            .where(PartnerPayoutRequest.id == payout_id)
            .with_for_update()
        )
        if not payout:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payout not found")

        before = payout.status.value
        payout.status = status_value
        payout.processed_by = actor.id
        payout.processed_at = datetime.now(UTC)
        if note is not None:
            payout.admin_note = note

        entry = self.db.scalar(
            select(PartnerLedgerEntry).where(
                PartnerLedgerEntry.reference_type == "partner_payout_request",
                PartnerLedgerEntry.reference_id == payout.id,
                PartnerLedgerEntry.entry_type == PartnerLedgerEntryType.PAYOUT,
            )
        )

        if status_value == PartnerPayoutStatus.PROCESSING and entry:
            entry.status = PartnerLedgerStatus.PROCESSING
        elif status_value == PartnerPayoutStatus.PAID and entry:
            entry.status = PartnerLedgerStatus.COMPLETED
        elif status_value in {PartnerPayoutStatus.REJECTED, PartnerPayoutStatus.CANCELLED}:
            if entry and entry.status in {
                PartnerLedgerStatus.RESERVED,
                PartnerLedgerStatus.PROCESSING,
            }:
                entry.status = PartnerLedgerStatus.VOIDED

        self.db.add(
            ReferralAuditEvent(
                actor_id=actor.id,
                action=f"payout.{status_value.value}",
                entity_type="partner_payout_request",
                entity_id=payout.id,
                note=note,
                before_json={"status": before},
                after_json={"status": status_value.value},
            )
        )
        self.db.commit()
        self.db.refresh(payout)
        return payout


class ReferralDashboardService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.ledger = ReferralLedgerService(db)

    def partner_overview(self, partner: ReferralPartner) -> dict:
        currency = self.settings.minimum_payout_currency.upper()
        clicks = self.db.scalar(
            select(func.count()).select_from(ReferralClick).where(
                ReferralClick.partner_id == partner.id
            )
        ) or 0
        registrations = self.db.scalar(
            select(func.count()).select_from(ReferralAttribution).where(
                ReferralAttribution.partner_id == partner.id,
                ReferralAttribution.locked_at.is_not(None),
            )
        ) or 0
        paid_enrollments = self.db.scalar(
            select(func.count(func.distinct(ReferralConversion.referred_user_id))).where(
                ReferralConversion.partner_id == partner.id,
                ReferralConversion.status.in_(
                    [
                        ReferralConversionStatus.PENDING,
                        ReferralConversionStatus.AVAILABLE,
                        ReferralConversionStatus.REVERSED,
                        ReferralConversionStatus.REVIEW_REQUIRED,
                    ]
                ),
            )
        ) or 0
        conversion_rate = (
            float(paid_enrollments) / float(registrations) if registrations else 0.0
        )
        return {
            "clicks": int(clicks),
            "registrations": int(registrations),
            "paid_enrollments": int(paid_enrollments),
            "conversion_rate": round(conversion_rate, 4),
            "pending_commission": self.ledger.pending_commission(
                partner_id=partner.id, currency=currency
            ),
            "available_balance": self.ledger.available_balance(
                partner_id=partner.id, currency=currency
            ),
            "total_paid_out": self.ledger.total_paid_out(
                partner_id=partner.id, currency=currency
            ),
            "currency": currency,
            "referral_code": partner.referral_code,
            "status": partner.status.value,
            "display_name": partner.display_name,
            "minimum_payout": referral_money(self.settings.minimum_payout_amount),
            "commission_rate": Decimal(self.settings.default_referral_commission_rate),
            "hold_days": self.settings.commission_hold_days,
        }

    def admin_overview(self) -> dict:
        currency = self.settings.minimum_payout_currency.upper()
        total_partners = self.db.scalar(select(func.count()).select_from(ReferralPartner)) or 0
        active = self.db.scalar(
            select(func.count()).select_from(ReferralPartner).where(
                ReferralPartner.status == ReferralPartnerStatus.ACTIVE
            )
        ) or 0
        pending_apps = self.db.scalar(
            select(func.count()).select_from(ReferralPartner).where(
                ReferralPartner.status == ReferralPartnerStatus.PENDING
            )
        ) or 0
        clicks = self.db.scalar(select(func.count()).select_from(ReferralClick)) or 0
        registrations = self.db.scalar(
            select(func.count()).select_from(ReferralAttribution).where(
                ReferralAttribution.locked_at.is_not(None)
            )
        ) or 0
        paid = self.db.scalar(
            select(func.count(func.distinct(ReferralConversion.referred_user_id))).where(
                ReferralConversion.status != ReferralConversionStatus.VOIDED
            )
        ) or 0
        pending_c = self.db.scalar(
            select(func.coalesce(func.sum(PartnerLedgerEntry.amount), 0)).where(
                PartnerLedgerEntry.entry_type == PartnerLedgerEntryType.COMMISSION,
                PartnerLedgerEntry.status == PartnerLedgerStatus.PENDING,
                PartnerLedgerEntry.currency == currency,
            )
        ) or 0
        available_c = self.db.scalar(
            select(func.coalesce(func.sum(PartnerLedgerEntry.amount), 0)).where(
                PartnerLedgerEntry.entry_type == PartnerLedgerEntryType.COMMISSION,
                PartnerLedgerEntry.status == PartnerLedgerStatus.AVAILABLE,
                PartnerLedgerEntry.currency == currency,
            )
        ) or 0
        paid_c = self.db.scalar(
            select(func.coalesce(func.sum(func.abs(PartnerLedgerEntry.amount)), 0)).where(
                PartnerLedgerEntry.entry_type == PartnerLedgerEntryType.PAYOUT,
                PartnerLedgerEntry.status == PartnerLedgerStatus.COMPLETED,
                PartnerLedgerEntry.currency == currency,
            )
        ) or 0
        return {
            "total_partners": int(total_partners),
            "active_partners": int(active),
            "pending_applications": int(pending_apps),
            "total_clicks": int(clicks),
            "total_registrations": int(registrations),
            "total_paid_enrollments": int(paid),
            "commission_pending": referral_money(pending_c),
            "commission_available": referral_money(available_c),
            "commission_paid": referral_money(paid_c),
            "currency": currency,
        }

    def leaderboard(self, *, period: str = "all", limit: int = 20) -> list[dict]:
        stmt = (
            select(
                ReferralPartner.id,
                ReferralPartner.display_name,
                func.count(func.distinct(ReferralConversion.referred_user_id)).label("enrollments"),
            )
            .join(ReferralConversion, ReferralConversion.partner_id == ReferralPartner.id)
            .where(
                ReferralPartner.status == ReferralPartnerStatus.ACTIVE,
                ReferralConversion.status.in_(
                    [
                        ReferralConversionStatus.PENDING,
                        ReferralConversionStatus.AVAILABLE,
                        ReferralConversionStatus.REVIEW_REQUIRED,
                    ]
                ),
            )
            .group_by(ReferralPartner.id, ReferralPartner.display_name)
            .order_by(func.count(func.distinct(ReferralConversion.referred_user_id)).desc())
            .limit(limit)
        )
        if period == "monthly":
            start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            stmt = stmt.where(ReferralConversion.created_at >= start)

        rows = self.db.execute(stmt).all()
        return [
            {
                "rank": i + 1,
                "display_name": row.display_name,
                "successful_enrollments": int(row.enrollments),
            }
            for i, row in enumerate(rows)
        ]
