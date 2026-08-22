from fastapi import Response

from app.core.config import Settings
from app.core.security import SecurityService


def _settings(**overrides: str) -> Settings:
    values = {
        "database_url": "postgresql://analyticsages:changeme@localhost:5432/analyticsages",
        "secret_key": "unit-test-secret-key-not-for-production",
        "frontend_url": "https://www.analyticsages.io",
        "environment": "development",
        "google_redirect_uri": "",
        **overrides,
    }
    return Settings(**values)


def test_cors_includes_apex_and_www():
    settings = _settings()
    assert "https://www.analyticsages.io" in settings.cors_origins
    assert "https://analyticsages.io" in settings.cors_origins


def test_production_refresh_cookie_is_first_party_lax():
    settings = _settings(environment="production")
    assert settings.refresh_cookie_samesite == "lax"
    assert settings.cookie_secure is True
    assert settings.refresh_cookie_path == "/"


def test_google_redirect_defaults_to_frontend_origin():
    settings = _settings()
    assert (
        settings.resolved_google_redirect_uri
        == "https://www.analyticsages.io/api/v1/auth/google/callback"
    )


def test_explicit_google_redirect_is_preserved():
    settings = _settings(google_redirect_uri="https://api.example.com/api/v1/auth/google/callback")
    assert settings.resolved_google_redirect_uri == (
        "https://api.example.com/api/v1/auth/google/callback"
    )


def test_refresh_cookie_is_set_on_site_root_path():
    settings = _settings(environment="production")
    security = SecurityService(settings)
    response = Response()
    security.set_refresh_cookie(response, "refresh-token")
    cookies = response.headers.getlist("set-cookie")
    set_headers = [row for row in cookies if "as_refresh_token=refresh-token" in row]
    assert set_headers
    header = set_headers[0].lower()
    assert "httponly" in header
    assert "samesite=lax" in header
    assert "secure" in header
    assert "path=/" in header
    assert "path=/api" not in header
