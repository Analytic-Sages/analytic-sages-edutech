"""Shared mock checkout/webhook helpers used when live API keys are absent."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any
from urllib.parse import urlencode

from fastapi import HTTPException, status

from app.core.config import Settings
from app.core.payments import PaymentProviderName, PaymentStatus
from app.payments.base import CheckoutRequest, CheckoutSession, WebhookEvent


def _mock_payment_id(provider: PaymentProviderName, order_id: str) -> str:
    return f"{provider.value}_{order_id}"


def create_mock_checkout(
    *,
    provider: PaymentProviderName,
    request: CheckoutRequest,
    frontend_url: str,
) -> CheckoutSession:
    provider_payment_id = _mock_payment_id(provider, request.order_id)
    query = urlencode(
        {
            "order_id": request.order_id,
            "provider": provider.value,
            "amount": str(request.amount),
            "currency": request.currency,
        }
    )
    checkout_url = f"{frontend_url.rstrip('/')}/checkout/mock?{query}"

    crypto_currency = None
    crypto_amount = None
    if provider == PaymentProviderName.NOWPAYMENTS:
        crypto_currency = "USDT"
        # Rough display estimate for mock UI only.
        crypto_amount = f"{max(request.amount / 100 / 1.0, 1):.2f}"

    return CheckoutSession(
        provider=provider,
        provider_payment_id=provider_payment_id,
        checkout_url=checkout_url,
        crypto_currency=crypto_currency,
        crypto_amount=crypto_amount,
        metadata={"mode": "mock"},
    )


def parse_mock_webhook(
    *,
    provider: PaymentProviderName,
    settings: Settings,
    headers: dict[str, str],
    body: bytes,
    payload: dict[str, Any],
) -> WebhookEvent:
    if settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mock payment webhooks are disabled in production",
        )

    expected = settings.mock_webhook_secret
    provided = headers.get("x-mock-signature") or headers.get("X-Mock-Signature")
    if expected:
        digest = hmac.new(expected.encode(), body, hashlib.sha256).hexdigest()
        if not provided or not hmac.compare_digest(digest, provided):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid mock webhook signature",
            )

    order_id = str(payload.get("order_id") or "")
    if not order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="order_id is required",
        )

    status_raw = str(payload.get("status") or PaymentStatus.CONFIRMED.value).lower()
    try:
        payment_status = PaymentStatus(status_raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported payment status: {status_raw}",
        ) from exc

    provider_payment_id = str(
        payload.get("provider_payment_id") or _mock_payment_id(provider, order_id)
    )

    return WebhookEvent(
        provider=provider,
        order_id=order_id,
        provider_payment_id=provider_payment_id,
        status=payment_status,
        crypto_currency=payload.get("crypto_currency"),
        crypto_amount=payload.get("crypto_amount"),
        raw=payload if payload else json.loads(body or b"{}"),
    )


class MockStripeProvider:
    name = PaymentProviderName.STRIPE

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_checkout(self, request: CheckoutRequest) -> CheckoutSession:
        return create_mock_checkout(
            provider=self.name,
            request=request,
            frontend_url=self.settings.frontend_url,
        )

    def verify_webhook(
        self,
        *,
        headers: dict[str, str],
        body: bytes,
        payload: dict[str, Any],
    ) -> WebhookEvent:
        return parse_mock_webhook(
            provider=self.name,
            settings=self.settings,
            headers=headers,
            body=body,
            payload=payload,
        )


class MockPaystackProvider:
    name = PaymentProviderName.PAYSTACK

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_checkout(self, request: CheckoutRequest) -> CheckoutSession:
        return create_mock_checkout(
            provider=self.name,
            request=request,
            frontend_url=self.settings.frontend_url,
        )

    def verify_webhook(
        self,
        *,
        headers: dict[str, str],
        body: bytes,
        payload: dict[str, Any],
    ) -> WebhookEvent:
        return parse_mock_webhook(
            provider=self.name,
            settings=self.settings,
            headers=headers,
            body=body,
            payload=payload,
        )


class MockNOWPaymentsProvider:
    name = PaymentProviderName.NOWPAYMENTS

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_checkout(self, request: CheckoutRequest) -> CheckoutSession:
        return create_mock_checkout(
            provider=self.name,
            request=request,
            frontend_url=self.settings.frontend_url,
        )

    def verify_webhook(
        self,
        *,
        headers: dict[str, str],
        body: bytes,
        payload: dict[str, Any],
    ) -> WebhookEvent:
        return parse_mock_webhook(
            provider=self.name,
            settings=self.settings,
            headers=headers,
            body=body,
            payload=payload,
        )
