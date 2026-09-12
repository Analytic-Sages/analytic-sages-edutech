"""Phone and ISO country validation helpers for user contact fields."""

from __future__ import annotations

import re

import phonenumbers
from fastapi import HTTPException, status
from phonenumbers import NumberParseException, PhoneNumberFormat

ISO2 = re.compile(r"^[A-Z]{2}$")

# ISO 3166-1 alpha-2 codes accepted for phone country and residence.
# Sourced from phonenumbers supported regions (excludes non-geo ZZ).
SUPPORTED_COUNTRY_CODES: frozenset[str] = frozenset(
    c for c in phonenumbers.SUPPORTED_REGIONS if len(c) == 2 and c.isalpha()
)


def normalize_iso2(value: str | None, *, field: str) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().upper()
    if not cleaned:
        return None
    if not ISO2.fullmatch(cleaned) or cleaned not in SUPPORTED_COUNTRY_CODES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid {field}",
        )
    return cleaned


def normalize_phone(
    phone_number: str | None,
    *,
    phone_country_code: str | None,
) -> tuple[str | None, str | None]:
    """Return (E.164 phone, ISO2 phone country) or (None, None) when cleared."""
    if phone_number is None or not str(phone_number).strip():
        return None, None

    region = normalize_iso2(phone_country_code, field="phone_country_code")
    raw = str(phone_number).strip()

    try:
        parsed = phonenumbers.parse(raw, region)
    except NumberParseException as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enter a valid phone number",
        ) from exc

    if not phonenumbers.is_possible_number(parsed) or not phonenumbers.is_valid_number(parsed):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enter a valid phone number",
        )

    e164 = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    region_code = phonenumbers.region_code_for_number(parsed)
    if not region_code:
        # Fall back to the selector region when libphonenumber cannot map (rare).
        if not region:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Select a phone country",
            )
        region_code = region

    return e164, region_code.upper()
