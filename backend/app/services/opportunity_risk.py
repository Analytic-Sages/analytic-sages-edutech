from __future__ import annotations

import re

from app.models.opportunity import RiskFlagSeverity
from app.services.opportunity_sources.base import RawOpportunity
from app.services.opportunity_urls import hostname_of, is_shortened_url

RULES: list[tuple[str, RiskFlagSeverity, str, tuple[str, ...]]] = [
    (
        "PAY_TO_APPLY",
        RiskFlagSeverity.CRITICAL,
        "Asks the applicant to pay to apply or secure the role.",
        ("pay to apply", "application fee", "processing fee to apply", "pay for this job"),
    ),
    (
        "CRYPTO_PAYMENT",
        RiskFlagSeverity.CRITICAL,
        "Asks the applicant to send crypto or tokens.",
        ("send crypto", "send usdt", "send bitcoin", "wallet payment", "pay in crypto"),
    ),
    (
        "GUARANTEED_INCOME",
        RiskFlagSeverity.HIGH,
        "Promises guaranteed income or risk-free returns.",
        ("guaranteed income", "guaranteed returns", "risk-free profit", "get rich"),
    ),
    (
        "URGENT_PAYMENT",
        RiskFlagSeverity.HIGH,
        "Creates urgency around a payment.",
        ("pay immediately", "urgent payment", "send payment now", "limited slots pay"),
    ),
    (
        "UNKNOWN_SOFTWARE",
        RiskFlagSeverity.HIGH,
        "Asks the applicant to install unknown software.",
        ("install this software", "download crack", "install unknown", "remote access tool"),
    ),
    (
        "SEED_PHRASE",
        RiskFlagSeverity.CRITICAL,
        "Asks for a wallet seed phrase or private key.",
        ("seed phrase", "private key", "recovery phrase", "secret recovery"),
    ),
    (
        "TELEGRAM_ONLY",
        RiskFlagSeverity.MEDIUM,
        "Contact is Telegram-only.",
        ("telegram only", "contact on telegram", "dm on telegram", "t.me/"),
    ),
]


def detect_risk_flags(raw: RawOpportunity) -> list[tuple[str, RiskFlagSeverity, str]]:
    text = " ".join(
        part for part in (raw.title, raw.description, raw.requirements, raw.application_url, raw.source_url or "") if part
    ).lower()
    flags: list[tuple[str, RiskFlagSeverity, str]] = []
    for flag_type, severity, description, patterns in RULES:
        if any(pattern in text for pattern in patterns):
            flags.append((flag_type, severity, description))

    url = raw.application_url or ""
    if not url:
        flags.append(("MISSING_URL", RiskFlagSeverity.HIGH, "No application URL was provided."))
    elif not re.match(r"^https?://", url, re.I):
        flags.append(("NON_HTTP_URL", RiskFlagSeverity.HIGH, "Application URL is not http(s)."))
    elif is_shortened_url(url):
        flags.append(
            ("SHORTENED_URL", RiskFlagSeverity.MEDIUM, f"Application URL uses a link shortener ({hostname_of(url)}).")
        )
    return flags
