"""Paystack adapter — Initialize Transaction + webhook (HMAC-SHA512).

Live mode activates when PAYSTACK_SECRET_KEY is set. Without a key, mock checkout
is used. Amounts are sent in currency subunits (kobo for NGN, cents for USD).
Enrollment unlocks on ``charge.success`` after signature + verify checks.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings
from app.core.payments import PaymentProviderName, PaymentStatus
from app.payments.base import CheckoutRequest, CheckoutSession, WebhookEvent
from app.payments.mock import MockPaystackProvider

logger = logging.getLogger(__name__)

SUPPORTED_CURRENCIES = frozenset({"NGN", "USD", "GHS", "ZAR", "KES"})


def resolve_paystack_charge(
    *,
    amount_major: int | float,
    currency: str,
    charge_currency: str,
    usd_to_ngn_rate: float,
) -> tuple[float, str]:
    """Map catalog price → Paystack charge currency/amount.

    If the merchant charges in NGN (default) and the catalog price is USD,
    convert with ``usd_to_ngn_rate``. Same-currency prices pass through.
    """
    catalog = (currency or "USD").upper()
    target = (charge_currency or catalog).upper()
    if target == catalog:
        return float(amount_major), catalog
    if catalog == "USD" and target == "NGN":
        return float(amount_major) * float(usd_to_ngn_rate), "NGN"
    if catalog == "NGN" and target == "USD":
        if not usd_to_ngn_rate:
            raise ValueError("usd_to_ngn_rate required to convert NGN→USD")
        return float(amount_major) / float(usd_to_ngn_rate), "USD"
    raise ValueError(f"Unsupported Paystack conversion {catalog}→{target}")


def to_paystack_subunit(amount_major: int | float, currency: str) -> int:
    """Catalog/charge prices are major units → Paystack subunits (kobo/cents)."""
    _ = currency
    return int(round(float(amount_major) * 100))


def from_paystack_subunit(amount_subunit: int | float | str, currency: str) -> float:
    _ = currency
    return float(amount_subunit) / 100.0


def verify_paystack_signature(*, body: bytes, signature: str, secret_key: str) -> bool:
    digest = hmac.new(secret_key.encode("utf-8"), body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(digest, signature)


class PaystackProvider:
    name = PaymentProviderName.PAYSTACK

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._mock = MockPaystackProvider(settings)

    @property
    def is_live(self) -> bool:
        return bool(self.settings.paystack_secret_key)

    def create_checkout(self, request: CheckoutRequest) -> CheckoutSession:
        if not self.is_live:
            return self._mock.create_checkout(request)
        return self._initialize_transaction(request)

    def verify_webhook(
        self,
        *,
        headers: dict[str, str],
        body: bytes,
        payload: dict[str, Any],
    ) -> WebhookEvent:
        if not self.is_live:
            return self._mock.verify_webhook(headers=headers, body=body, payload=payload)
        return self._verify_webhook(headers=headers, body=body, payload=payload)

    def _api_base(self) -> str:
        return (self.settings.paystack_api_url or "https://api.paystack.co").rstrip("/")

    def _initialize_transaction(self, request: CheckoutRequest) -> CheckoutSession:
        secret = self.settings.paystack_secret_key
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Paystack is not configured",
            )

        try:
            charge_amount, currency = resolve_paystack_charge(
                amount_major=request.amount,
                currency=request.currency or "USD",
                charge_currency=self.settings.paystack_charge_currency,
                usd_to_ngn_rate=self.settings.paystack_usd_to_ngn_rate,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        if currency not in SUPPORTED_CURRENCIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Paystack does not support currency {currency}",
            )

        # Paystack reference: alphanumeric plus - . =  (no underscore)
        reference = request.order_id.replace("_", "-")
        amount_subunit = to_paystack_subunit(charge_amount, currency)

        body = {
            "email": request.customer_email,
            "amount": amount_subunit,
            "currency": currency,
            "reference": reference,
            "callback_url": request.success_url,
            "metadata": {
                "order_id": request.order_id,
                "title": request.course_title,
                "catalog_amount": request.amount,
                "catalog_currency": (request.currency or "").upper(),
                "charge_amount": charge_amount,
                "charge_currency": currency,
                **(request.metadata or {}),
            },
        }

        url = f"{self._api_base()}/transaction/initialize"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {secret}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
        except httpx.HTTPError as exc:
            logger.exception("Paystack initialize request failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to reach Paystack",
            ) from exc

        if response.status_code >= 400:
            detail = "Paystack rejected the checkout request"
            try:
                err = response.json()
                if isinstance(err, dict) and err.get("message"):
                    detail = str(err["message"])
            except ValueError:
                pass
            logger.error(
                "Paystack initialize error status=%s body=%s",
                response.status_code,
                response.text[:500],
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=detail,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid Paystack response",
            ) from exc

        if not payload.get("status"):
            logger.error("Paystack initialize unsuccessful: %s", payload)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=payload.get("message") or "Paystack initialize failed",
            )

        data = payload.get("data") or {}
        auth_url = data.get("authorization_url")
        ref = data.get("reference") or reference
        if not auth_url:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Paystack did not return an authorization URL",
            )

        return CheckoutSession(
            provider=self.name,
            provider_payment_id=str(ref),
            checkout_url=str(auth_url),
            metadata={
                "mode": "live",
                "reference": str(ref),
                "access_code": data.get("access_code"),
                "amount_subunit": amount_subunit,
                "currency": currency,
                "charge_amount": charge_amount,
                "charge_currency": currency,
                "catalog_amount": request.amount,
                "catalog_currency": (request.currency or "").upper(),
            },
        )

    def _verify_webhook(
        self,
        *,
        headers: dict[str, str],
        body: bytes,
        payload: dict[str, Any],
    ) -> WebhookEvent:
        secret = self.settings.paystack_secret_key
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Paystack is not configured",
            )

        signature = headers.get("x-paystack-signature") or ""
        if not signature or not verify_paystack_signature(
            body=body, signature=signature, secret_key=secret
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Paystack signature",
            )

        event = str(payload.get("event") or "")
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        reference = str(
            data.get("reference")
            or (data.get("metadata") or {}).get("order_id")
            or ""
        ).strip()
        if not reference:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Paystack webhook missing reference",
            )

        # Prefer live verify so we do not trust webhook body alone for fulfillment.
        verified = self._fetch_verified_transaction(reference)
        order_id = self._order_id_from_reference(reference, verified, data)

        paystack_status = str(verified.get("status") or data.get("status") or "").lower()
        payment_status = self._map_status(event=event, paystack_status=paystack_status)

        return WebhookEvent(
            provider=self.name,
            order_id=order_id,
            provider_payment_id=str(verified.get("id") or reference),
            status=payment_status,
            crypto_currency=None,
            crypto_amount=None,
            raw={
                "event": event,
                "webhook": payload,
                "verified": verified,
            },
        )

    def _fetch_verified_transaction(self, reference: str) -> dict[str, Any]:
        secret = self.settings.paystack_secret_key
        url = f"{self._api_base()}/transaction/verify/{reference}"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    url,
                    headers={"Authorization": f"Bearer {secret}"},
                )
        except httpx.HTTPError as exc:
            logger.exception("Paystack verify failed for ref=%s", reference)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to verify Paystack transaction",
            ) from exc

        if response.status_code >= 400:
            logger.error(
                "Paystack verify error status=%s body=%s",
                response.status_code,
                response.text[:500],
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Paystack transaction verify failed",
            )

        payload = response.json()
        if not payload.get("status"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=payload.get("message") or "Paystack verify unsuccessful",
            )
        data = payload.get("data")
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid Paystack verify payload",
            )
        return data

    @staticmethod
    def _order_id_from_reference(
        reference: str,
        verified: dict[str, Any],
        webhook_data: dict[str, Any],
    ) -> str:
        meta = verified.get("metadata") or webhook_data.get("metadata") or {}
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                meta = {}
        if isinstance(meta, dict) and meta.get("order_id"):
            return str(meta["order_id"])
        return reference

    @staticmethod
    def _map_status(*, event: str, paystack_status: str) -> PaymentStatus:
        if event == "charge.success" and paystack_status == "success":
            return PaymentStatus.CONFIRMED
        if event in {"charge.failed", "paymentrequest.failed"} or paystack_status in {
            "failed",
            "reversed",
        }:
            return PaymentStatus.FAILED
        if paystack_status in {"abandoned", "ongoing"}:
            return PaymentStatus.PENDING
        return PaymentStatus.PENDING
