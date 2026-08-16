"""Stripe adapter — uses mock checkout until STRIPE_SECRET_KEY is configured."""

from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.core.payments import PaymentProviderName
from app.payments.base import CheckoutRequest, CheckoutSession, WebhookEvent
from app.payments.mock import MockStripeProvider


class StripeProvider:
    name = PaymentProviderName.STRIPE

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._mock = MockStripeProvider(settings)

    @property
    def is_live(self) -> bool:
        return bool(self.settings.stripe_secret_key)

    def create_checkout(self, request: CheckoutRequest) -> CheckoutSession:
        if not self.is_live:
            return self._mock.create_checkout(request)
        # Live Stripe Checkout Session creation — wire when keys are available.
        raise NotImplementedError(
            "Live Stripe checkout is not enabled yet. Unset STRIPE_SECRET_KEY to use mock mode."
        )

    def verify_webhook(
        self,
        *,
        headers: dict[str, str],
        body: bytes,
        payload: dict[str, Any],
    ) -> WebhookEvent:
        if not self.is_live:
            return self._mock.verify_webhook(headers=headers, body=body, payload=payload)
        raise NotImplementedError(
            "Live Stripe webhooks are not enabled yet. Unset STRIPE_SECRET_KEY to use mock mode."
        )
