"""USD reporting estimates for referral commissions — informational only.

Financial ledger amounts stay in the payment/commission currency.
These helpers never settle FX or rewrite ledger balances.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

from app.core.config import Settings
from app.core.referrals import referral_money


def _parse_decimal_map(raw: str | None) -> dict[str, Decimal]:
    if not raw or not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, Decimal] = {}
    for key, value in data.items():
        try:
            out[str(key).upper()] = Decimal(str(value))
        except Exception:
            continue
    return out


def reporting_fx_rates(settings: Settings) -> dict[str, Decimal]:
    """USD per 1 unit of currency (admin-configured static rates)."""
    rates = _parse_decimal_map(settings.referral_reporting_fx_rates_json)
    rates.setdefault("USD", Decimal("1"))
    rates.setdefault("USDT", Decimal("1"))
    rates.setdefault("USDC", Decimal("1"))
    if "NGN" not in rates:
        ngn_per_usd = Decimal(str(settings.paystack_usd_to_ngn_rate or "1600"))
        if ngn_per_usd > 0:
            rates["NGN"] = Decimal("1") / ngn_per_usd
    return rates


def minimum_payout_thresholds(settings: Settings) -> dict[str, Decimal]:
    """Per-currency payout minima. No mixed-currency aggregation."""
    configured = _parse_decimal_map(settings.minimum_payout_thresholds_json)
    if configured:
        return {k: referral_money(v) for k, v in configured.items()}

    usd_min = referral_money(settings.default_global_minimum_payout_usd_equivalent)
    rates = reporting_fx_rates(settings)
    thresholds: dict[str, Decimal] = {"USD": usd_min, "USDT": usd_min, "USDC": usd_min}
    ngn_rate = rates.get("NGN")
    if ngn_rate and ngn_rate > 0:
        thresholds["NGN"] = referral_money(usd_min / ngn_rate)
    # Preserve legacy single-currency override when thresholds not explicitly set
    legacy_ccy = settings.minimum_payout_currency.upper()
    legacy_amt = referral_money(settings.minimum_payout_amount)
    thresholds.setdefault(legacy_ccy, legacy_amt)
    return thresholds


def estimate_usd(
    *,
    amount: Decimal | int | str,
    currency: str,
    settings: Settings,
    at: datetime | None = None,
) -> tuple[Decimal | None, Decimal | None, datetime]:
    """Return (usd_equivalent, fx_rate, timestamp). None if no rate for currency."""
    currency = currency.upper()
    rates = reporting_fx_rates(settings)
    rate = rates.get(currency)
    stamp = at or datetime.now(UTC)
    if rate is None:
        return None, None, stamp
    usd = referral_money(Decimal(str(amount)) * rate)
    return usd, rate, stamp


def safe_referral_redirect(path: str | None, *, default: str) -> str:
    """Allow only same-origin relative paths (open-redirect hardening)."""
    candidate = (path or default or "/programs").strip() or default
    if not candidate.startswith("/"):
        return default
    if candidate.startswith("//") or "\\" in candidate or "://" in candidate:
        return default
    if any(ch in candidate for ch in ("\n", "\r", "\0")):
        return default
    return candidate
