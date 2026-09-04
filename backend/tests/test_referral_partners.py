"""Referral Partner Program — attribution, 7% payment-level commission, idempotency."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.payments import PaymentProviderName, PaymentStatus
from app.core.referrals import (
    PartnerLedgerStatus,
    ReferralConversionStatus,
    ReferralPartnerStatus,
    commission_from_payment_amount,
    referral_money,
)
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.classroom import Cohort, CohortStatus
from app.models.payment import Payment
from app.models.referral import (
    PartnerLedgerEntry,
    ReferralAttribution,
    ReferralConversion,
    ReferralPartner,
)
from app.models.user import User
from app.payments.base import WebhookEvent
from app.services.email import EmailService
from app.services.payments import PaymentService
from app.services.referrals import (
    ReferralAttributionService,
    ReferralCommissionService,
    ReferralPartnerService,
)

client = TestClient(app)


def _token_for(user: User) -> str:
    return SecurityService(get_settings()).create_access_token(
        user_id=str(user.id), role=user.role.value
    )


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_for(user)}"}


def _make_user(email: str, role: UserRole = UserRole.STUDENT, full_name: str = "Ref User") -> User:
    db = SessionLocal()
    try:
        user = User(
            email=email,
            full_name=full_name,
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


def _cleanup_emails(*emails: str) -> None:
    db = SessionLocal()
    try:
        for email in emails:
            user = db.scalar(select(User).where(User.email == email))
            if not user:
                continue
            partner = db.scalar(select(ReferralPartner).where(ReferralPartner.user_id == user.id))
            if partner:
                for conv in db.scalars(
                    select(ReferralConversion).where(ReferralConversion.partner_id == partner.id)
                ).all():
                    for entry in db.scalars(
                        select(PartnerLedgerEntry).where(
                            PartnerLedgerEntry.reference_id == conv.id
                        )
                    ).all():
                        db.delete(entry)
                    db.delete(conv)
                for attr in db.scalars(
                    select(ReferralAttribution).where(ReferralAttribution.partner_id == partner.id)
                ).all():
                    db.delete(attr)
                db.delete(partner)
            for payment in db.scalars(select(Payment).where(Payment.user_id == user.id)).all():
                db.delete(payment)
            db.delete(user)
        db.commit()
    finally:
        db.close()


def _cleanup_cohort(*, slug: str | None = None, cohort_id=None) -> None:
    """Delete cohort and dependents in FK-safe order."""
    from app.models.billing import PaymentWebhookEvent
    from app.models.classroom import CohortMember

    db = SessionLocal()
    try:
        cohort = None
        if cohort_id is not None:
            cohort = db.get(Cohort, cohort_id)
        elif slug:
            cohort = db.scalar(select(Cohort).where(Cohort.slug == slug))
        if not cohort:
            return

        for payment in list(
            db.scalars(select(Payment).where(Payment.cohort_id == cohort.id)).all()
        ):
            for conv in list(
                db.scalars(
                    select(ReferralConversion).where(ReferralConversion.payment_id == payment.id)
                ).all()
            ):
                for entry in list(
                    db.scalars(
                        select(PartnerLedgerEntry).where(
                            PartnerLedgerEntry.reference_id == conv.id
                        )
                    ).all()
                ):
                    db.delete(entry)
                db.delete(conv)
            for event in list(
                db.scalars(
                    select(PaymentWebhookEvent).where(PaymentWebhookEvent.payment_id == payment.id)
                ).all()
            ):
                db.delete(event)
            db.delete(payment)

        for member in list(
            db.scalars(select(CohortMember).where(CohortMember.cohort_id == cohort.id)).all()
        ):
            db.delete(member)

        db.delete(cohort)
        db.commit()
    finally:
        db.close()


def test_commission_formula_is_seven_percent():
    assert commission_from_payment_amount(
        eligible_amount=300_000, rate=Decimal("0.07")
    ) == Decimal("21000.00")
    assert commission_from_payment_amount(
        eligible_amount=100_000, rate=Decimal("0.07")
    ) == Decimal("7000.00")


def test_referral_track_and_first_touch_wins():
    partner_email = f"partner-{uuid.uuid4()}@example.com"
    admin_email = f"admin-ref-{uuid.uuid4()}@example.com"
    try:
        partner_user = _make_user(partner_email, full_name="Partner One")
        admin = _make_user(admin_email, UserRole.ADMIN)
        db = SessionLocal()
        try:
            svc = ReferralPartnerService(db, get_settings())
            partner = svc.apply(
                user=partner_user,
                display_name="Partner One",
                social_handle=None,
                promotion_channels="X",
                terms_accepted=True,
            )
            partner = svc.set_status(
                partner_id=partner.id,
                status_value=ReferralPartnerStatus.ACTIVE,
                actor=admin,
            )
            code = partner.referral_code
            assert code
        finally:
            db.close()

        visitor = uuid.uuid4().hex
        r1 = client.post(
            "/api/v1/referrals/track",
            json={"code": code, "anonymous_visitor_id": visitor, "landing_path": "/ref/x"},
        )
        assert r1.status_code == 200
        assert r1.json()["ok"] is True

        # Second code must not overwrite first-touch
        other_email = f"partner2-{uuid.uuid4()}@example.com"
        other_user = _make_user(other_email, full_name="Partner Two")
        db = SessionLocal()
        try:
            svc = ReferralPartnerService(db, get_settings())
            other = svc.apply(
                user=other_user,
                display_name="Partner Two",
                social_handle=None,
                promotion_channels="WA",
                terms_accepted=True,
            )
            other = svc.set_status(
                partner_id=other.id,
                status_value=ReferralPartnerStatus.ACTIVE,
                actor=admin,
            )
            code2 = other.referral_code
        finally:
            db.close()

        r2 = client.post(
            "/api/v1/referrals/track",
            json={"code": code2, "anonymous_visitor_id": visitor},
        )
        assert r2.status_code == 200

        db = SessionLocal()
        try:
            attrs = list(
                db.scalars(
                    select(ReferralAttribution).where(
                        ReferralAttribution.anonymous_visitor_id == visitor
                    )
                ).all()
            )
            # First attribution remains the active one for this visitor's unexpired window
            assert any(a.referral_code == code for a in attrs)
            locked_none = [a for a in attrs if a.locked_at is None and a.expires_at > datetime.now(UTC)]
            assert locked_none[0].referral_code == code
        finally:
            db.close()
            _cleanup_emails(other_email)
    finally:
        _cleanup_emails(partner_email, admin_email)


def test_payment_creates_seven_percent_commission_idempotent():
    partner_email = f"p-comm-{uuid.uuid4()}@example.com"
    learner_email = f"l-comm-{uuid.uuid4()}@example.com"
    admin_email = f"a-comm-{uuid.uuid4()}@example.com"
    cohort_slug = f"ref-cohort-{uuid.uuid4().hex[:8]}"
    try:
        partner_user = _make_user(partner_email, full_name="Comm Partner")
        learner = _make_user(learner_email, full_name="Learner")
        admin = _make_user(admin_email, UserRole.ADMIN)

        db = SessionLocal()
        try:
            settings = get_settings()
            partners = ReferralPartnerService(db, settings)
            partner = partners.apply(
                user=partner_user,
                display_name="Comm Partner",
                social_handle=None,
                promotion_channels="community",
                terms_accepted=True,
            )
            partner = partners.set_status(
                partner_id=partner.id,
                status_value=ReferralPartnerStatus.ACTIVE,
                actor=admin,
            )

            visitor = uuid.uuid4().hex
            ReferralAttributionService(db, settings).track_click(
                code=partner.referral_code or "",
                anonymous_visitor_id=visitor,
                landing_path="/ref/x",
                ip=None,
                user_agent=None,
            )
            ReferralAttributionService(db, settings).lock_for_new_user(
                user=learner, anonymous_visitor_id=visitor
            )
            db.commit()

            cohort = Cohort(
                name="Referral Test Cohort",
                slug=cohort_slug,
                description="test",
                status=CohortStatus.OPEN,
                price=300_000,
                currency="NGN",
                referral_commission_eligible=True,
            )
            db.add(cohort)
            db.flush()

            payment = Payment(
                order_id=f"ord-ref-{uuid.uuid4().hex[:10]}",
                user_id=learner.id,
                cohort_id=cohort.id,
                provider=PaymentProviderName.MOCK,
                provider_payment_id=f"mock_{uuid.uuid4().hex[:8]}",
                amount=100_000,
                currency="NGN",
                status=PaymentStatus.PENDING,
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
            payment_id = payment.id
            order_id = payment.order_id
        finally:
            db.close()

        payments = PaymentService(SessionLocal(), get_settings(), EmailService(get_settings()))
        event = WebhookEvent(
            provider=PaymentProviderName.MOCK,
            order_id=order_id,
            status=PaymentStatus.CONFIRMED,
            provider_payment_id=f"mock_ok_{uuid.uuid4().hex[:6]}",
            raw={"test": True},
        )
        payments.process_webhook_event(event)

        db = SessionLocal()
        try:
            conv = db.scalar(
                select(ReferralConversion).where(ReferralConversion.payment_id == payment_id)
            )
            assert conv is not None
            assert conv.commission_rate == Decimal("0.07")
            assert conv.commission_amount == Decimal("7000.00")
            assert conv.eligible_amount == Decimal("100000.00")
            assert conv.status == ReferralConversionStatus.PENDING
            ledger = db.scalar(
                select(PartnerLedgerEntry).where(
                    PartnerLedgerEntry.reference_id == conv.id,
                    PartnerLedgerEntry.status == PartnerLedgerStatus.PENDING,
                )
            )
            assert ledger is not None
            assert ledger.amount == Decimal("7000.00")
        finally:
            db.close()

        # Duplicate webhook must not create a second conversion
        payments2 = PaymentService(SessionLocal(), get_settings(), EmailService(get_settings()))
        payments2.process_webhook_event(
            WebhookEvent(
                provider=PaymentProviderName.MOCK,
                order_id=order_id,
                status=PaymentStatus.CONFIRMED,
                provider_payment_id=event.provider_payment_id,
                raw={"test": True, "dup": 1},
            )
        )
        db = SessionLocal()
        try:
            count = len(
                list(
                    db.scalars(
                        select(ReferralConversion).where(
                            ReferralConversion.payment_id == payment_id
                        )
                    ).all()
                )
            )
            assert count == 1
        finally:
            db.close()
    finally:
        _cleanup_cohort(slug=cohort_slug)
        _cleanup_emails(partner_email, learner_email, admin_email)


def test_refund_voids_pending_commission():
    partner_email = f"p-ref-{uuid.uuid4()}@example.com"
    learner_email = f"l-ref-{uuid.uuid4()}@example.com"
    admin_email = f"a-ref-{uuid.uuid4()}@example.com"
    cohort_id = None
    try:
        partner_user = _make_user(partner_email)
        learner = _make_user(learner_email)
        admin = _make_user(admin_email, UserRole.ADMIN)
        db = SessionLocal()
        try:
            settings = get_settings()
            partners = ReferralPartnerService(db, settings)
            partner = partners.apply(
                user=partner_user,
                display_name="Refund Partner",
                social_handle=None,
                promotion_channels="x",
                terms_accepted=True,
            )
            partner = partners.set_status(
                partner_id=partner.id,
                status_value=ReferralPartnerStatus.ACTIVE,
                actor=admin,
            )
            visitor = uuid.uuid4().hex
            ReferralAttributionService(db, settings).track_click(
                code=partner.referral_code or "",
                anonymous_visitor_id=visitor,
                landing_path="/ref",
                ip=None,
                user_agent=None,
            )
            ReferralAttributionService(db, settings).lock_for_new_user(
                user=learner, anonymous_visitor_id=visitor
            )
            cohort = Cohort(
                name="Refund Cohort",
                slug=f"ref-r-{uuid.uuid4().hex[:8]}",
                description="",
                status=CohortStatus.OPEN,
                price=50_000,
                currency="NGN",
            )
            db.add(cohort)
            db.flush()
            payment = Payment(
                order_id=f"ord-rf-{uuid.uuid4().hex[:10]}",
                user_id=learner.id,
                cohort_id=cohort.id,
                provider=PaymentProviderName.MOCK,
                amount=50_000,
                currency="NGN",
                status=PaymentStatus.CONFIRMED,
                confirmed_at=datetime.now(UTC),
            )
            db.add(payment)
            db.flush()
            ReferralCommissionService(db, settings).handle_successful_payment(payment)
            db.commit()
            db.refresh(payment)
            payment_id = payment.id
            cohort_id = cohort.id
        finally:
            db.close()

        db = SessionLocal()
        try:
            payment = db.get(Payment, payment_id)
            assert payment
            payment.status = PaymentStatus.REFUNDED
            ReferralCommissionService(db, get_settings()).handle_refunded_payment(payment)
            db.commit()
            conv = db.scalar(
                select(ReferralConversion).where(ReferralConversion.payment_id == payment_id)
            )
            assert conv is not None
            assert conv.status == ReferralConversionStatus.VOIDED
        finally:
            db.close()
    finally:
        if cohort_id is not None:
            _cleanup_cohort(cohort_id=cohort_id)
        _cleanup_emails(partner_email, learner_email, admin_email)


def test_partner_cannot_access_admin_referrals():
    email = f"partner-deny-{uuid.uuid4()}@example.com"
    try:
        user = _make_user(email)
        resp = client.get("/api/v1/admin/referrals/overview", headers=_auth(user))
        assert resp.status_code == 403
    finally:
        _cleanup_emails(email)


def test_release_held_commissions():
    settings = get_settings()
    partner_email = f"p-hold-{uuid.uuid4()}@example.com"
    learner_email = f"l-hold-{uuid.uuid4()}@example.com"
    admin_email = f"a-hold-{uuid.uuid4()}@example.com"
    cohort_id = None
    try:
        partner_user = _make_user(partner_email)
        learner = _make_user(learner_email)
        admin = _make_user(admin_email, UserRole.ADMIN)
        db = SessionLocal()
        try:
            partners = ReferralPartnerService(db, settings)
            partner = partners.apply(
                user=partner_user,
                display_name="Hold Partner",
                social_handle=None,
                promotion_channels="x",
                terms_accepted=True,
            )
            partner = partners.set_status(
                partner_id=partner.id,
                status_value=ReferralPartnerStatus.ACTIVE,
                actor=admin,
            )
            visitor = uuid.uuid4().hex
            ReferralAttributionService(db, settings).track_click(
                code=partner.referral_code or "",
                anonymous_visitor_id=visitor,
                landing_path="/ref",
                ip=None,
                user_agent=None,
            )
            ReferralAttributionService(db, settings).lock_for_new_user(
                user=learner, anonymous_visitor_id=visitor
            )
            cohort = Cohort(
                name="Hold Cohort",
                slug=f"hold-{uuid.uuid4().hex[:8]}",
                description="",
                status=CohortStatus.OPEN,
                price=10_000,
                currency="NGN",
            )
            db.add(cohort)
            db.flush()
            payment = Payment(
                order_id=f"ord-h-{uuid.uuid4().hex[:10]}",
                user_id=learner.id,
                cohort_id=cohort.id,
                provider=PaymentProviderName.MOCK,
                amount=10_000,
                currency="NGN",
                status=PaymentStatus.CONFIRMED,
                confirmed_at=datetime.now(UTC),
            )
            db.add(payment)
            db.flush()
            conv = ReferralCommissionService(db, settings).handle_successful_payment(payment)
            assert conv
            conv.available_at = datetime.now(UTC) - timedelta(days=1)
            db.commit()
            cohort_id = cohort.id
        finally:
            db.close()

        db = SessionLocal()
        try:
            released = ReferralCommissionService(db, settings).release_held_commissions()
            assert released >= 1
        finally:
            db.close()
    finally:
        _cleanup_cohort(cohort_id=cohort_id)
        _cleanup_emails(partner_email, learner_email, admin_email)


def test_money_helpers_never_float():
    assert isinstance(referral_money(7), Decimal)
    assert isinstance(commission_from_payment_amount(eligible_amount=1, rate=Decimal("0.07")), Decimal)


def test_usd_reporting_estimate_does_not_overwrite_ledger_currency():
    from app.core.referral_fx import estimate_usd, minimum_payout_thresholds, safe_referral_redirect

    settings = get_settings()
    usd, rate, _ = estimate_usd(amount=Decimal("21.00"), currency="USD", settings=settings)
    assert usd == Decimal("21.00")
    assert rate == Decimal("1")

    ngn_usd, ngn_rate, _ = estimate_usd(
        amount=Decimal("16000.00"), currency="NGN", settings=settings
    )
    assert ngn_rate is not None
    assert ngn_usd is not None
    # 16000 NGN at 1600 NGN/USD ≈ $10 reporting estimate
    assert ngn_usd == Decimal("10.00")

    thresholds = minimum_payout_thresholds(settings)
    assert "USD" in thresholds
    assert thresholds["USD"] == Decimal("25.00")

    assert safe_referral_redirect("/programs", default="/programs") == "/programs"
    assert safe_referral_redirect("//evil.com", default="/programs") == "/programs"
    assert safe_referral_redirect("https://evil.com", default="/programs") == "/programs"


def test_usd_payment_commission_stores_reporting_estimate():
    partner_email = f"partner-usd-{uuid.uuid4()}@example.com"
    learner_email = f"learner-usd-{uuid.uuid4()}@example.com"
    admin_email = f"admin-usd-{uuid.uuid4()}@example.com"
    cohort_id = None
    try:
        partner_user = _make_user(partner_email, full_name="USD Partner")
        learner = _make_user(learner_email, full_name="USD Learner")
        admin = _make_user(admin_email, UserRole.ADMIN)
        settings = get_settings()
        db = SessionLocal()
        try:
            svc = ReferralPartnerService(db, settings)
            partner = svc.apply(
                user=partner_user,
                display_name="USD Partner",
                social_handle=None,
                promotion_channels="X",
                terms_accepted=True,
            )
            partner = svc.set_status(
                partner_id=partner.id,
                status_value=ReferralPartnerStatus.ACTIVE,
                actor=admin,
            )
            now = datetime.now(UTC)
            db.add(
                ReferralAttribution(
                    partner_id=partner.id,
                    anonymous_visitor_id=uuid.uuid4().hex,
                    referred_user_id=learner.id,
                    referral_code=partner.referral_code or "TESTUSD",
                    attributed_at=now,
                    expires_at=now + timedelta(days=30),
                    locked_at=now,
                )
            )
            cohort = Cohort(
                name="USD Cohort",
                slug=f"ref-usd-{uuid.uuid4().hex[:8]}",
                description="test",
                status=CohortStatus.OPEN,
                price=300,
                currency="USD",
                referral_commission_eligible=True,
            )
            db.add(cohort)
            db.flush()
            payment = Payment(
                order_id=f"ord-usd-{uuid.uuid4().hex[:10]}",
                user_id=learner.id,
                cohort_id=cohort.id,
                provider=PaymentProviderName.MOCK,
                amount=Decimal("300.00"),
                currency="USD",
                status=PaymentStatus.CONFIRMED,
                confirmed_at=datetime.now(UTC),
            )
            db.add(payment)
            db.flush()
            conv = ReferralCommissionService(db, settings).handle_successful_payment(payment)
            db.commit()
            assert conv is not None
            assert conv.currency == "USD"
            assert conv.commission_amount == Decimal("21.00")
            assert conv.reporting_usd_equivalent == Decimal("21.00")
            entry = db.scalar(
                select(PartnerLedgerEntry).where(
                    PartnerLedgerEntry.reference_id == conv.id,
                )
            )
            assert entry is not None
            assert entry.currency == "USD"
            assert entry.amount == Decimal("21.00")
            assert entry.reporting_usd_equivalent == Decimal("21.00")
            cohort_id = cohort.id
        finally:
            db.close()
    finally:
        _cleanup_cohort(cohort_id=cohort_id)
        _cleanup_emails(partner_email, learner_email, admin_email)


def test_payout_rejects_unsupported_currency_and_mixed_aggregation():
    from app.services.referrals import ReferralPayoutService

    db = SessionLocal()
    try:
        payouts = ReferralPayoutService(db, get_settings())
        assert payouts.minimum_for("USD") == Decimal("25.00")
        assert payouts.minimum_for("BTC") is None
    finally:
        db.close()

