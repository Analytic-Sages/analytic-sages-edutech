"""Tests for optional user phone and country of residence fields."""

from app.services.phone import normalize_iso2, normalize_phone


def test_normalize_phone_nigeria():
    phone, country = normalize_phone("8012345678", phone_country_code="NG")
    assert phone == "+2348012345678"
    assert country == "NG"


def test_normalize_phone_e164_preserves_country():
    phone, country = normalize_phone("+12015551234", phone_country_code="NG")
    assert phone == "+12015551234"
    assert country == "US"


def test_normalize_phone_empty():
    phone, country = normalize_phone("", phone_country_code="NG")
    assert phone is None
    assert country is None


def test_normalize_residence_independent():
    assert normalize_iso2("gb", field="country_of_residence") == "GB"
    assert normalize_iso2(None, field="country_of_residence") is None
