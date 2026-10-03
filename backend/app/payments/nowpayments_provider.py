"""NOWPayments adapter — invoice checkout + IPN (HMAC-SHA512).

Live mode activates when NOWPAYMENTS_API_KEY is set. Without a key, mock checkout
is used (local MVP). Enrollment unlocks only on IPN status ``finished``.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings
from app.core.payments import PaymentProviderName, PaymentStatus
from app.payments.base import CheckoutRequest, CheckoutSession, WebhookEvent
from app.payments.mock import MockNOWPaymentsProvider

logger = logging.getLogger(__name__)

# NOWPayments payment_status → internal PaymentStatus.
# Unlock enrollment only on ``finished`` (funds settled). Do not unlock on
# confirming/confirmed/partially_paid — matches NOWPayments guidance.
_STATUS_MAP: dict[str, PaymentStatus] = {
    "waiting": PaymentStatus.PENDING,
    "sending": PaymentStatus.PENDING,
    "confirming": PaymentStatus.CONFIRMING,
    "confirmed": PaymentStatus.CONFIRMING,
    "finished": PaymentStatus.CONFIRMED,
    "partially_paid": PaymentStatus.CONFIRMING,
    "failed": PaymentStatus.FAILED,
    "refunded": PaymentStatus.REFUNDED,
    "expired": PaymentStatus.EXPIRED,
}


def sort_object_deep(value: Any) -> Any:
    """Recursively sort dict keys for NOWPayments IPN signature canonicalization."""
    if isinstance(value, dict):
        return {key: sort_object_deep(value[key]) for key in sorted(value.keys())}
    if isinstance(value, list):
        return [sort_object_deep(item) for item in value]
    return value


def canonical_ipn_json(payload: dict[str, Any]) -> str:
    """Python-style canonical form: json.dumps(sortObjectDeep(payload))."""
    return json.dumps(sort_object_deep(payload), separators=(",", ":"), ensure_ascii=False)


def _js_number(value: float) -> str:
    """Format a float the way JavaScript's JSON.stringify does.

    The differences that matter for HMAC canonicalization:
    - integral floats: JS writes 35 for 35.0 (Python: "35.0")
    - exponents: JS writes 1e-7 (Python: "1e-07", zero-padded exponent)
    """
    if value.is_integer() and abs(value) < 1e21:
        return str(int(value))
    text = repr(value)
    if "e" in text or "E" in text:
        mantissa, _, exponent = text.lower().partition("e")
        sign = ""
        if exponent.startswith(("+", "-")):
            sign, exponent = exponent[0], exponent[1:]
        exponent = exponent.lstrip("0") or "0"
        text = f"{mantissa}e{sign}{exponent}"
    return text


def _js_dumps(value: Any) -> str:
    """Minimal JSON.stringify-equivalent serializer (sorted keys, compact)."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _js_number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ",".join(_js_dumps(item) for item in value) + "]"
    if isinstance(value, dict):
        items = sorted(value.items(), key=lambda pair: str(pair[0]))
        return "{" + ",".join(
            json.dumps(str(key), ensure_ascii=False) + ":" + _js_dumps(item)
            for key, item in items
        ) + "}"
    raise TypeError(f"Unsupported type in IPN payload: {type(value)!r}")


def canonical_ipn_json_js(payload: dict[str, Any]) -> str:
    """JS-style canonical form: JSON.stringify(sortObjectDeep(payload))."""
    return _js_dumps(payload)


def verify_nowpayments_signature(*, payload: dict[str, Any], signature: str, ipn_secret: str) -> bool:
    """Accept the signature computed over either canonical form.

    NOWPayments' own docs show Node/PHP/Python examples whose float formatting
    differs, and their payload may contain integral floats (e.g. price_amount
    35.0). Accepting both deterministic canonical forms of the same payload
    keeps verification strict (still HMAC-checked) without rejecting valid IPNs.
    """
    for canonical in {canonical_ipn_json(payload), canonical_ipn_json_js(payload)}:
        digest = hmac.new(
            ipn_secret.encode("utf-8"),
            canonical.encode("utf-8"),
            hashlib.sha512,
        ).hexdigest()
        if hmac.compare_digest(digest, signature):
            return True
    return False


def map_nowpayments_status(raw: str | None) -> PaymentStatus:
    if not raw:
        return PaymentStatus.PENDING
    key = raw.strip().lower()
    if key in _STATUS_MAP:
        return _STATUS_MAP[key]
    # Unknown statuses stay pending so we never unlock incorrectly.
    logger.warning("Unknown NOWPayments payment_status=%s", raw)
    return PaymentStatus.PENDING


def fiat_price_amount(amount: int | float | Decimal, currency: str) -> float:
    """Convert stored course price to NOWPayments price_amount (major units).

    Catalog amounts are whole major units (e.g. 35 USD), not cents.
    """
    _ = currency  # reserved if we later store minor units for some currencies
    return float(Decimal(str(amount)))


class NOWPaymentsProvider:
    name = PaymentProviderName.NOWPAYMENTS

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._mock = MockNOWPaymentsProvider(settings)

    @property
    def is_live(self) -> bool:
        return bool(self.settings.nowpayments_api_key)

    def create_checkout(self, request: CheckoutRequest) -> CheckoutSession:
        if not self.is_live:
            return self._mock.create_checkout(request)
        return self._create_invoice(request)

    def verify_webhook(
        self,
        *,
        headers: dict[str, str],
        body: bytes,
        payload: dict[str, Any],
    ) -> WebhookEvent:
        if not self.is_live:
            return self._mock.verify_webhook(headers=headers, body=body, payload=payload)
        return self._verify_ipn(headers=headers, body=body, payload=payload)

    def _ipn_callback_url(self) -> str:
        base = (self.settings.public_api_url or "http://localhost:8000").rstrip("/")
        return f"{base}/api/v1/webhooks/payments/nowpayments"

    def fetch_payment_by_id(self, payment_id: str) -> dict[str, Any] | None:
        """GET Payment Status (api-key auth). Used for admin reconciliation of missed IPNs."""
        api_key = self.settings.nowpayments_api_key
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="NOWPayments is not configured",
            )

        url = f"{self.settings.nowpayments_api_url.rstrip('/')}/payment/{payment_id}"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers={"x-api-key": api_key})
        except httpx.HTTPError as exc:
            logger.exception("NOWPayments payment lookup failed payment_id=%s", payment_id)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to reach NOWPayments",
            ) from exc

        if response.status_code == 404:
            return None

        if response.status_code >= 400:
            logger.error(
                "NOWPayments payment lookup error payment_id=%s status=%s body=%s",
                payment_id,
                response.status_code,
                response.text[:500],
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="NOWPayments rejected the payment lookup",
            )

        try:
            return response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid NOWPayments payment lookup response",
            ) from exc

    def find_payment_for_order(self, order_id: str) -> dict[str, Any] | None:
        """Scan GET /v1/payment/ (list payments) for a record matching our order_id.

        Lets us reconcile automatically when the IPN was missed, without anyone
        having to copy a payment ID out of the NOWPayments dashboard.
        """
        api_key = self.settings.nowpayments_api_key
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="NOWPayments is not configured",
            )

        base = self.settings.nowpayments_api_url.rstrip("/")
        try:
            with httpx.Client(timeout=15.0) as client:
                for page in range(3):  # scan the 300 most-recent payments
                    response = client.get(
                        f"{base}/payment/",
                        headers={"x-api-key": api_key},
                        params={
                            "limit": 100,
                            "page": page,
                            "sortBy": "created_at",
                            "orderBy": "desc",
                        },
                    )
                    if response.status_code >= 400:
                        logger.error(
                            "NOWPayments list payments error order_id=%s status=%s body=%s",
                            order_id,
                            response.status_code,
                            response.text[:500],
                        )
                        return None
                    items = response.json().get("data") or []
                    for record in items:
                        if str(record.get("order_id") or "") == order_id:
                            return record
                    if len(items) < 100:
                        return None
        except httpx.HTTPError:
            logger.exception("NOWPayments list payments failed order_id=%s", order_id)
        return None

    def _create_invoice(self, request: CheckoutRequest) -> CheckoutSession:
        api_key = self.settings.nowpayments_api_key
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="NOWPayments is not configured",
            )

        price_currency = (
            self.settings.nowpayments_price_currency or request.currency or "USD"
        ).lower()
        body = {
            "price_amount": fiat_price_amount(request.amount, request.currency),
            "price_currency": price_currency,
            "order_id": request.order_id,
            "order_description": request.course_title[:400],
            "ipn_callback_url": self._ipn_callback_url(),
            "success_url": request.success_url,
            "cancel_url": request.cancel_url,
        }

        url = f"{self.settings.nowpayments_api_url.rstrip('/')}/invoice"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    url,
                    headers={
                        "x-api-key": api_key,
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
        except httpx.HTTPError as exc:
            logger.exception("NOWPayments invoice request failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to reach NOWPayments",
            ) from exc

        if response.status_code >= 400:
            logger.error(
                "NOWPayments invoice error status=%s body=%s",
                response.status_code,
                response.text[:500],
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="NOWPayments rejected the invoice request",
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid NOWPayments invoice response",
            ) from exc

        invoice_id = data.get("id")
        invoice_url = data.get("invoice_url")
        if not invoice_id or not invoice_url:
            logger.error("NOWPayments invoice missing id/url: %s", data)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="NOWPayments invoice response incomplete",
            )

        return CheckoutSession(
            provider=self.name,
            provider_payment_id=str(invoice_id),
            checkout_url=str(invoice_url),
            crypto_currency=_as_optional_str(data.get("pay_currency")),
            crypto_amount=_as_optional_str(data.get("pay_amount")),
            metadata={
                "mode": "live",
                "invoice_id": str(invoice_id),
                "price_amount": body["price_amount"],
                "price_currency": price_currency,
            },
        )

    def _verify_ipn(
        self,
        *,
        headers: dict[str, str],
        body: bytes,
        payload: dict[str, Any],
    ) -> WebhookEvent:
        _ = body  # signature is over sorted JSON of the parsed payload
        ipn_secret = self.settings.nowpayments_ipn_secret
        if not ipn_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="NOWPayments IPN secret is not configured",
            )

        signature = headers.get("x-nowpayments-sig") or headers.get("x-nowpayments-signature")
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing NOWPayments signature",
            )

        if not verify_nowpayments_signature(
            payload=payload,
            signature=signature,
            ipn_secret=ipn_secret,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid NOWPayments signature",
            )

        order_id = str(payload.get("order_id") or "").strip()
        if not order_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="order_id missing from NOWPayments IPN",
            )

        payment_status = map_nowpayments_status(
            str(payload.get("payment_status") or payload.get("status") or "")
        )

        provider_payment_id = str(
            payload.get("payment_id")
            or payload.get("invoice_id")
            or payload.get("id")
            or order_id
        )

        return WebhookEvent(
            provider=self.name,
            order_id=order_id,
            provider_payment_id=provider_payment_id,
            status=payment_status,
            crypto_currency=_as_optional_str(payload.get("pay_currency")),
            crypto_amount=_as_optional_str(payload.get("pay_amount")),
            raw=payload,
        )


def _as_optional_str(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def amounts_match(*, expected: int | float, reported: Any, tolerance: Decimal = Decimal("0.01")) -> bool:
    """Compare fiat price_amount from IPN to our stored order amount."""
    if reported is None or reported == "":
        return True  # some early IPNs omit price; do not hard-fail
    try:
        left = Decimal(str(expected))
        right = Decimal(str(reported))
    except (InvalidOperation, ValueError):
        return False
    return abs(left - right) <= tolerance
