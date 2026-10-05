"""PaymentService — in-flight checkout reuse + NOWPayments auto-reconcile."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.core.payments import PaymentProviderName, PaymentStatus
from app.models.payment import Payment
from app.services.payments import PaymentService


def _settings(**overrides) -> Settings:
    base = dict(
        database_url="postgresql://analyticsages:changeme@localhost:5434/analyticsages",
        secret_key="dev-secret-key-for-local-testing-only-32chars",
        environment="development",
        frontend_url="http://localhost:3000",
        public_api_url="https://api.example.com",
        payment_mode="mock",
        mock_webhook_secret="",
        paystack_secret_key=None,
        nowpayments_api_key=None,
        nowpayments_ipn_secret=None,
    )
    base.update(overrides)
    return Settings(**base)


def _service(db: MagicMock | None = None, settings: Settings | None = None) -> PaymentService:
    return PaymentService(db or MagicMock(), settings or _settings(), MagicMock())


def _payment(**overrides) -> Payment:
    base = dict(
        id=uuid4(),
        order_id="ord_stuck1",
        user_id=uuid4(),
        course_id=None,
        cohort_id=uuid4(),
        billing_account_id=None,
        payment_obligation_id=None,
        provider=PaymentProviderName.NOWPAYMENTS,
        provider_payment_id="4522625843",
        amount=200,
        currency="USD",
        crypto_currency=None,
        crypto_amount=None,
        status=PaymentStatus.PENDING,
        checkout_url="https://nowpayments.io/payment/?iid=4522625843",
        metadata_json={},
        confirmed_at=None,
        created_at=datetime.now(UTC),
    )
    base.update(overrides)
    return Payment(**base)


def test_checkout_response_for_payment_marks_nowpayments_mock_without_key():
    payment = _payment()
    response = _service()._checkout_response_for_payment(payment)
    assert response.order_id == "ord_stuck1"
    assert response.checkout_url == payment.checkout_url
    assert response.mode == "mock"
    assert response.cohort_id == payment.cohort_id


def test_checkout_response_for_payment_live_when_key_set():
    payment = _payment()
    service = _service(settings=_settings(nowpayments_api_key="live-key"))
    response = service._checkout_response_for_payment(payment)
    assert response.mode == "live"


def test_find_in_flight_payment_returns_most_recent():
    older = _payment(order_id="ord_old", created_at=datetime.now(UTC) - timedelta(hours=2))
    newer = _payment(order_id="ord_new", created_at=datetime.now(UTC) - timedelta(minutes=5))
    db = MagicMock()
    db.scalar.return_value = newer
    service = _service(db=db)
    found = service._find_in_flight_payment(
        user_id=newer.user_id,
        provider_name=PaymentProviderName.NOWPAYMENTS,
        course_id=None,
        cohort_id=newer.cohort_id,
    )
    assert found is not None
    assert found.order_id == "ord_new"
    assert older is not newer


def test_find_in_flight_payment_needs_a_target():
    service = _service()
    assert (
        service._find_in_flight_payment(
            user_id=uuid4(),
            provider_name=PaymentProviderName.NOWPAYMENTS,
            course_id=None,
            cohort_id=None,
        )
        is None
    )


def test_auto_reconcile_skips_when_not_nowpayments():
    payment = _payment(provider=PaymentProviderName.PAYSTACK)
    service = _service()
    service._reconcile_nowpayments_payment = MagicMock()  # type: ignore[method-assign]
    service._maybe_auto_reconcile(payment)
    service._reconcile_nowpayments_payment.assert_not_called()


def test_auto_reconcile_skips_terminal_status():
    payment = _payment(status=PaymentStatus.CONFIRMED)
    service = _service(settings=_settings(nowpayments_api_key="live-key"))
    service._reconcile_nowpayments_payment = MagicMock()  # type: ignore[method-assign]
    service._maybe_auto_reconcile(payment)
    service._reconcile_nowpayments_payment.assert_not_called()


def test_auto_reconcile_skips_without_api_key():
    payment = _payment()
    service = _service(settings=_settings(nowpayments_api_key=None))
    service._reconcile_nowpayments_payment = MagicMock()  # type: ignore[method-assign]
    service._maybe_auto_reconcile(payment)
    service._reconcile_nowpayments_payment.assert_not_called()


def test_auto_reconcile_skips_fresh_payment():
    payment = _payment(created_at=datetime.now(UTC) - timedelta(seconds=30))
    service = _service(settings=_settings(nowpayments_api_key="live-key"))
    service._reconcile_nowpayments_payment = MagicMock()  # type: ignore[method-assign]
    service._maybe_auto_reconcile(payment)
    service._reconcile_nowpayments_payment.assert_not_called()


def test_auto_reconcile_throttled_by_metadata_marker():
    payment = _payment(
        created_at=datetime.now(UTC) - timedelta(minutes=10),
        metadata_json={"last_auto_reconcile_at": datetime.now(UTC).isoformat()},
    )
    service = _service(settings=_settings(nowpayments_api_key="live-key"))
    service._reconcile_nowpayments_payment = MagicMock()  # type: ignore[method-assign]
    service._maybe_auto_reconcile(payment)
    service._reconcile_nowpayments_payment.assert_not_called()


def test_auto_reconcile_triggers_lookup_and_swallows_http_errors():
    payment = _payment(created_at=datetime.now(UTC) - timedelta(minutes=10))
    service = _service(settings=_settings(nowpayments_api_key="live-key"))
    service._reconcile_nowpayments_payment = MagicMock(  # type: ignore[method-assign]
        side_effect=HTTPException(status_code=404, detail="No NOWPayments payment found")
    )
    service._maybe_auto_reconcile(payment)
    service._reconcile_nowpayments_payment.assert_called_once_with(payment, payment_id=None)
    assert payment.metadata_json is not None
    assert "last_auto_reconcile_at" in payment.metadata_json


def test_get_payment_for_user_runs_auto_reconcile():
    payment = _payment(created_at=datetime.now(UTC) - timedelta(minutes=10))
    db = MagicMock()
    db.scalar.return_value = payment
    service = _service(db=db, settings=_settings(nowpayments_api_key="live-key"))
    service._reconcile_nowpayments_payment = MagicMock()  # type: ignore[method-assign]
    user = MagicMock(id=payment.user_id)
    result = service.get_payment_for_user(user=user, order_id=payment.order_id)
    assert result.order_id == payment.order_id
    service._reconcile_nowpayments_payment.assert_called_once_with(payment, payment_id=None)


def test_reconcile_stale_sweep_skips_without_api_key():
    service = _service(settings=_settings(nowpayments_api_key=None))
    assert service.reconcile_stale_nowpayments() == {
        "scanned": 0,
        "confirmed": 0,
        "updated": 0,
        "failed": 0,
    }


def test_reconcile_stale_sweep_confirms_and_updates():
    a = _payment(order_id="ord_a", status=PaymentStatus.PENDING)
    b = _payment(order_id="ord_b", status=PaymentStatus.CONFIRMING)
    db = MagicMock()
    db.scalars.return_value.all.return_value = [a, b]
    service = _service(db=db, settings=_settings(nowpayments_api_key="live-key"))

    def fake(payment, *, payment_id):
        assert payment_id is None
        payment.status = (
            PaymentStatus.CONFIRMED if payment.order_id == "ord_a" else PaymentStatus.EXPIRED
        )
        return payment

    service._reconcile_nowpayments_payment = MagicMock(side_effect=fake)  # type: ignore[method-assign]
    summary = service.reconcile_stale_nowpayments(older_than_seconds=60, limit=10)
    assert summary["scanned"] == 2
    assert summary["confirmed"] == 1
    assert summary["updated"] == 1
    assert summary["failed"] == 0


def test_reconcile_stale_sweep_ignores_404_but_counts_other_failures():
    a = _payment(order_id="ord_a")
    b = _payment(order_id="ord_b")
    db = MagicMock()
    db.scalars.return_value.all.return_value = [a, b]
    service = _service(db=db, settings=_settings(nowpayments_api_key="live-key"))

    def fake(payment, *, payment_id):
        if payment.order_id == "ord_a":
            raise HTTPException(status_code=404, detail="customer never sent funds")
        raise HTTPException(status_code=502, detail="provider down")

    service._reconcile_nowpayments_payment = MagicMock(side_effect=fake)  # type: ignore[method-assign]
    summary = service.reconcile_stale_nowpayments()
    assert summary["scanned"] == 2
    assert summary["failed"] == 1
    assert summary["confirmed"] == 0
