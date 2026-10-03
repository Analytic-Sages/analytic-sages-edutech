"""NOWPayments provider tests — mock fallback + live invoice/IPN logic."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.core.payments import PaymentProviderName, PaymentStatus
from app.payments.base import CheckoutRequest
from app.payments.factory import get_payment_provider
from app.payments.nowpayments_provider import (
    amounts_match,
    canonical_ipn_json,
    canonical_ipn_json_js,
    map_nowpayments_status,
    verify_nowpayments_signature,
)


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


def _checkout_request() -> CheckoutRequest:
    return CheckoutRequest(
        order_id="ord_test123",
        amount=35,
        currency="USD",
        course_title="SQL Blockchain Data Analytics",
        customer_email="student@example.com",
        success_url="http://localhost:3000/checkout/success",
        cancel_url="http://localhost:3000/checkout/cancel",
    )


def test_mock_checkout_when_api_key_absent():
    settings = _settings()
    provider = get_payment_provider(PaymentProviderName.NOWPAYMENTS, settings)
    session = provider.create_checkout(_checkout_request())
    assert session.provider == PaymentProviderName.NOWPAYMENTS
    assert "checkout/mock" in session.checkout_url


def test_map_nowpayments_status():
    assert map_nowpayments_status("finished") == PaymentStatus.CONFIRMED
    assert map_nowpayments_status("confirming") == PaymentStatus.CONFIRMING
    assert map_nowpayments_status("confirmed") == PaymentStatus.CONFIRMING
    assert map_nowpayments_status("partially_paid") == PaymentStatus.CONFIRMING
    assert map_nowpayments_status("failed") == PaymentStatus.FAILED
    assert map_nowpayments_status("expired") == PaymentStatus.EXPIRED
    assert map_nowpayments_status("waiting") == PaymentStatus.PENDING
    assert map_nowpayments_status("unknown_xyz") == PaymentStatus.PENDING


def test_amounts_match():
    assert amounts_match(expected=35, reported=35)
    assert amounts_match(expected=35, reported="35.00")
    assert amounts_match(expected=35, reported=None)
    assert not amounts_match(expected=35, reported=34)


def test_ipn_signature_roundtrip():
    secret = "test-ipn-secret"
    payload = {
        "payment_id": 123456789,
        "payment_status": "finished",
        "order_id": "ord_test123",
        "price_amount": 35,
        "price_currency": "usd",
        "pay_amount": 35.1,
        "pay_currency": "usdttrc20",
        "fee": {"currency": "usd", "depositFee": 0.5},
    }
    import hashlib
    import hmac

    digest = hmac.new(
        secret.encode(),
        canonical_ipn_json(payload).encode(),
        hashlib.sha512,
    ).hexdigest()
    assert verify_nowpayments_signature(payload=payload, signature=digest, ipn_secret=secret)
    assert not verify_nowpayments_signature(
        payload=payload, signature="deadbeef", ipn_secret=secret
    )


def test_js_canonical_formats_floats_like_json_stringify():
    payload = {"a": 35.0, "b": 0.001, "c": 1e-7, "d": "usd", "e": None}
    assert canonical_ipn_json_js(payload) == '{"a":35,"b":0.001,"c":1e-7,"d":"usd","e":null}'
    # Python canonical keeps the float form — this is the mismatch we guard against.
    assert '"a":35.0' in canonical_ipn_json(payload)


def test_ipn_signature_accepts_js_signed_payload_with_integral_floats():
    """NOWPayments signs with JSON.stringify semantics: 35.0 serializes as 35.
    A payload parsed from JSON with integral floats must still verify."""
    secret = "test-ipn-secret"
    payload = {
        "payment_id": 123456789,
        "payment_status": "finished",
        "order_id": "ord_test123",
        "price_amount": 35.0,
        "actually_paid": 35.1,
        "outcome_amount": 34.8,
        "fee": {"depositFee": 0.09853637216235617, "withdrawalFee": 0.0, "serviceFee": 0.5},
    }
    import hashlib
    import hmac

    js_digest = hmac.new(
        secret.encode(),
        canonical_ipn_json_js(payload).encode(),
        hashlib.sha512,
    ).hexdigest()
    assert verify_nowpayments_signature(payload=payload, signature=js_digest, ipn_secret=secret)

    py_digest = hmac.new(
        secret.encode(),
        canonical_ipn_json(payload).encode(),
        hashlib.sha512,
    ).hexdigest()
    assert verify_nowpayments_signature(payload=payload, signature=py_digest, ipn_secret=secret)
    assert not verify_nowpayments_signature(
        payload=payload, signature="deadbeef", ipn_secret=secret
    )


def test_live_verify_ipn_success():
    secret = "test-ipn-secret"
    payload = {
        "payment_id": 987,
        "invoice_id": 555,
        "payment_status": "finished",
        "order_id": "ord_test123",
        "price_amount": 35,
        "pay_currency": "btc",
        "pay_amount": 0.001,
    }
    import hashlib
    import hmac

    signature = hmac.new(
        secret.encode(),
        canonical_ipn_json(payload).encode(),
        hashlib.sha512,
    ).hexdigest()

    settings = _settings(
        nowpayments_api_key="live-key",
        nowpayments_ipn_secret=secret,
    )
    provider = get_payment_provider(PaymentProviderName.NOWPAYMENTS, settings)
    event = provider.verify_webhook(
        headers={"x-nowpayments-sig": signature},
        body=b"{}",
        payload=payload,
    )
    assert event.order_id == "ord_test123"
    assert event.status == PaymentStatus.CONFIRMED
    assert event.provider_payment_id == "987"
    assert event.crypto_currency == "btc"


def test_live_verify_ipn_rejects_bad_signature():
    settings = _settings(
        nowpayments_api_key="live-key",
        nowpayments_ipn_secret="test-ipn-secret",
    )
    provider = get_payment_provider(PaymentProviderName.NOWPAYMENTS, settings)
    with pytest.raises(HTTPException) as exc:
        provider.verify_webhook(
            headers={"x-nowpayments-sig": "nope"},
            body=b"{}",
            payload={"order_id": "ord_test123", "payment_status": "finished"},
        )
    assert exc.value.status_code == 401


def test_live_create_invoice_posts_to_nowpayments():
    settings = _settings(
        nowpayments_api_key="live-key",
        nowpayments_ipn_secret="ipn-secret",
        nowpayments_api_url="https://api.nowpayments.io/v1",
    )
    provider = get_payment_provider(PaymentProviderName.NOWPAYMENTS, settings)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "4522625843",
        "invoice_url": "https://nowpayments.io/payment/?iid=4522625843",
        "order_id": "ord_test123",
        "price_amount": 35,
        "price_currency": "usd",
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_response

    with patch("app.payments.nowpayments_provider.httpx.Client", return_value=mock_client):
        session = provider.create_checkout(_checkout_request())

    assert session.checkout_url == "https://nowpayments.io/payment/?iid=4522625843"
    assert session.provider_payment_id == "4522625843"
    assert session.metadata["mode"] == "live"

    args, kwargs = mock_client.post.call_args
    assert args[0] == "https://api.nowpayments.io/v1/invoice"
    assert kwargs["headers"]["x-api-key"] == "live-key"
    assert kwargs["json"]["order_id"] == "ord_test123"
    assert kwargs["json"]["price_amount"] == 35.0
    assert kwargs["json"]["ipn_callback_url"] == (
        "https://api.example.com/api/v1/webhooks/payments/nowpayments"
    )


def test_fetch_payment_by_id_returns_record():
    settings = _settings(
        nowpayments_api_key="live-key",
        nowpayments_ipn_secret="ipn-secret",
        nowpayments_api_url="https://api.nowpayments.io/v1",
    )
    provider = get_payment_provider(PaymentProviderName.NOWPAYMENTS, settings)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "order_id": "ord_test123",
        "payment_id": 987,
        "payment_status": "finished",
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    with patch("app.payments.nowpayments_provider.httpx.Client", return_value=mock_client):
        record = provider.fetch_payment_by_id("987")

    assert record is not None
    assert record["payment_id"] == 987
    args, kwargs = mock_client.get.call_args
    assert args[0] == "https://api.nowpayments.io/v1/payment/987"
    assert kwargs["headers"]["x-api-key"] == "live-key"


def test_find_payment_for_order_matches_order_id():
    settings = _settings(
        nowpayments_api_key="live-key",
        nowpayments_ipn_secret="ipn-secret",
        nowpayments_api_url="https://api.nowpayments.io/v1",
    )
    provider = get_payment_provider(PaymentProviderName.NOWPAYMENTS, settings)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"payment_id": 111, "order_id": "ord_other", "payment_status": "finished"},
            {"payment_id": 987, "order_id": "ord_test123", "payment_status": "finished"},
        ]
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    with patch("app.payments.nowpayments_provider.httpx.Client", return_value=mock_client):
        record = provider.find_payment_for_order("ord_test123")

    assert record is not None
    assert record["payment_id"] == 987
    args, kwargs = mock_client.get.call_args
    assert args[0] == "https://api.nowpayments.io/v1/payment/"
    assert kwargs["headers"]["x-api-key"] == "live-key"


def test_find_payment_for_order_returns_none_when_absent():
    settings = _settings(
        nowpayments_api_key="live-key",
        nowpayments_ipn_secret="ipn-secret",
    )
    provider = get_payment_provider(PaymentProviderName.NOWPAYMENTS, settings)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [{"payment_id": 111, "order_id": "ord_other", "payment_status": "finished"}]
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    with patch("app.payments.nowpayments_provider.httpx.Client", return_value=mock_client):
        record = provider.find_payment_for_order("ord_test123")

    assert record is None


def test_find_payment_for_order_returns_none_on_api_error():
    settings = _settings(
        nowpayments_api_key="live-key",
        nowpayments_ipn_secret="ipn-secret",
    )
    provider = get_payment_provider(PaymentProviderName.NOWPAYMENTS, settings)

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    with patch("app.payments.nowpayments_provider.httpx.Client", return_value=mock_client):
        record = provider.find_payment_for_order("ord_test123")

    assert record is None


def test_fetch_payment_by_id_returns_none_on_404():
    settings = _settings(
        nowpayments_api_key="live-key",
        nowpayments_ipn_secret="ipn-secret",
    )
    provider = get_payment_provider(PaymentProviderName.NOWPAYMENTS, settings)

    mock_response = MagicMock()
    mock_response.status_code = 404

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    with patch("app.payments.nowpayments_provider.httpx.Client", return_value=mock_client):
        record = provider.fetch_payment_by_id("does-not-exist")

    assert record is None


def test_mock_paystack_when_secret_absent():
    settings = _settings()
    provider = get_payment_provider(PaymentProviderName.PAYSTACK, settings)
    session = provider.create_checkout(_checkout_request())
    assert "checkout/mock" in session.checkout_url


def test_to_paystack_subunit():
    from app.payments.paystack_provider import to_paystack_subunit

    assert to_paystack_subunit(35, "USD") == 3500
    assert to_paystack_subunit(5000, "NGN") == 500000


def test_resolve_paystack_charge_usd_to_ngn():
    from app.payments.paystack_provider import resolve_paystack_charge

    amount, currency = resolve_paystack_charge(
        amount_major=35,
        currency="USD",
        charge_currency="NGN",
        usd_to_ngn_rate=1600,
    )
    assert currency == "NGN"
    assert amount == 56000.0


def test_live_paystack_initialize():
    settings = _settings(
        paystack_secret_key="sk_test_xxx",
        paystack_charge_currency="NGN",
        paystack_usd_to_ngn_rate=1600,
    )
    provider = get_payment_provider(PaymentProviderName.PAYSTACK, settings)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": True,
        "data": {
            "authorization_url": "https://checkout.paystack.com/abc",
            "access_code": "access",
            "reference": "ord-test123",
        },
    }
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_response

    with patch("app.payments.paystack_provider.httpx.Client", return_value=mock_client):
        session = provider.create_checkout(_checkout_request())

    assert session.checkout_url == "https://checkout.paystack.com/abc"
    assert session.metadata["mode"] == "live"
    assert session.metadata["charge_currency"] == "NGN"
    args, kwargs = mock_client.post.call_args
    assert args[0] == "https://api.paystack.co/transaction/initialize"
    assert kwargs["json"]["amount"] == 5_600_000  # ₦56,000 in kobo
    assert kwargs["json"]["currency"] == "NGN"
    assert kwargs["headers"]["Authorization"] == "Bearer sk_test_xxx"


def test_live_paystack_webhook_success():
    import hashlib
    import hmac

    secret = "sk_test_xxx"
    body = (
        b'{"event":"charge.success","data":{"reference":"ord-test123","status":"success",'
        b'"amount":3500,"currency":"USD","metadata":{"order_id":"ord-test123"}}}'
    )
    signature = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    payload = {
        "event": "charge.success",
        "data": {
            "reference": "ord-test123",
            "status": "success",
            "amount": 3500,
            "currency": "USD",
            "metadata": {"order_id": "ord-test123"},
        },
    }

    settings = _settings(paystack_secret_key=secret)
    provider = get_payment_provider(PaymentProviderName.PAYSTACK, settings)

    verify_response = MagicMock()
    verify_response.status_code = 200
    verify_response.json.return_value = {
        "status": True,
        "data": {
            "id": 999,
            "status": "success",
            "reference": "ord-test123",
            "amount": 3500,
            "currency": "USD",
            "metadata": {"order_id": "ord-test123"},
        },
    }
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = verify_response

    with patch("app.payments.paystack_provider.httpx.Client", return_value=mock_client):
        event = provider.verify_webhook(
            headers={"x-paystack-signature": signature},
            body=body,
            payload=payload,
        )

    assert event.order_id == "ord-test123"
    assert event.status == PaymentStatus.CONFIRMED


def test_live_paystack_webhook_bad_signature():
    settings = _settings(paystack_secret_key="sk_test_xxx")
    provider = get_payment_provider(PaymentProviderName.PAYSTACK, settings)
    with pytest.raises(HTTPException) as exc:
        provider.verify_webhook(
            headers={"x-paystack-signature": "nope"},
            body=b'{"event":"charge.success"}',
            payload={"event": "charge.success", "data": {"reference": "ord-x"}},
        )
    assert exc.value.status_code == 401
