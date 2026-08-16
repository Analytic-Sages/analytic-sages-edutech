from dataclasses import dataclass, field
from typing import Any, Protocol

from app.core.payments import PaymentProviderName, PaymentStatus


@dataclass
class CheckoutRequest:
    order_id: str
    amount: int
    currency: str
    course_title: str
    customer_email: str
    success_url: str
    cancel_url: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckoutSession:
    provider: PaymentProviderName
    provider_payment_id: str
    checkout_url: str
    crypto_currency: str | None = None
    crypto_amount: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WebhookEvent:
    provider: PaymentProviderName
    order_id: str
    provider_payment_id: str
    status: PaymentStatus
    crypto_currency: str | None = None
    crypto_amount: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class PaymentProvider(Protocol):
    name: PaymentProviderName

    def create_checkout(self, request: CheckoutRequest) -> CheckoutSession: ...

    def verify_webhook(
        self,
        *,
        headers: dict[str, str],
        body: bytes,
        payload: dict[str, Any],
    ) -> WebhookEvent: ...
