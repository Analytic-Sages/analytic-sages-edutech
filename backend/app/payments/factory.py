from fastapi import HTTPException, status

from app.core.config import Settings
from app.core.payments import PaymentProviderName
from app.payments.base import PaymentProvider
from app.payments.nowpayments_provider import NOWPaymentsProvider
from app.payments.paystack_provider import PaystackProvider
from app.payments.stripe_provider import StripeProvider


def get_payment_provider(name: PaymentProviderName, settings: Settings) -> PaymentProvider:
    if name == PaymentProviderName.STRIPE:
        return StripeProvider(settings)
    if name == PaymentProviderName.PAYSTACK:
        return PaystackProvider(settings)
    if name == PaymentProviderName.NOWPAYMENTS:
        return NOWPaymentsProvider(settings)
    if name == PaymentProviderName.MOCK:
        # Generic mock routes through Stripe mock for checkout URL shape.
        return StripeProvider(settings)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported payment provider: {name}",
    )
