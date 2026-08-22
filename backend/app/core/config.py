import logging
from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "staging", "production"] = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: PostgresDsn
    redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")

    secret_key: str = Field(min_length=32)
    frontend_url: str = "http://localhost:3000"
    # Public base URL of this API (no trailing slash). Used for NOWPayments IPN callbacks.
    # Localhost will not receive IPNs unless you use a tunnel (ngrok, etc.).
    public_api_url: str = "http://localhost:8000"

    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    email_verification_expire_hours: int = 24
    password_reset_expire_hours: int = 1
    invite_expire_hours: int = 168

    cookie_secure: bool = False
    cookie_domain: str | None = None
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    # Path=/ so the refresh cookie is sent on page loads and same-origin /api calls.
    refresh_cookie_path: str = "/"

    auth_rate_limit_requests: int = 10
    auth_rate_limit_window_seconds: int = 60

    email_from: str = "noreply@analyticsages.com"
    email_api_key: str | None = None
    contact_email: str = "support@analyticsages.io"
    # Resend Audience ID (dashboard may label this Segment). Used for Insights subscribe + issue sends.
    resend_audience_id: str | None = None

    # Google OAuth — leave empty to use mock Google login in development.
    # Redirect URI should be the public site origin (same-origin API rewrite), not the API host.
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None

    # Payments — leave keys empty to force mock adapters (recommended for local MVP)
    payment_mode: Literal["mock", "live"] = "mock"
    mock_webhook_secret: str = "dev-mock-webhook-secret"
    paystack_secret_key: str | None = None
    paystack_api_url: str = "https://api.paystack.co"
    # Most NG merchants settle in NGN. USD catalog prices convert at this rate for Paystack.
    paystack_charge_currency: str = "NGN"
    paystack_usd_to_ngn_rate: float = 1600.0
    nowpayments_api_key: str | None = None
    nowpayments_ipn_secret: str | None = None
    nowpayments_api_url: str = "https://api.nowpayments.io/v1"
    nowpayments_price_currency: str = "USD"

    # Cloudflare RealtimeKit (live classroom) — leave empty for mock join mode
    cloudflare_account_id: str | None = None
    cloudflare_api_token: str | None = None
    realtimekit_app_id: str | None = None
    realtimekit_host_preset: str = "group_call_host"
    realtimekit_participant_preset: str = "group_call_participant"

    # Local article image uploads (dev / API disk). Not Postgres.
    storage_dir: str = "var/uploads"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def refresh_cookie_name(self) -> str:
        return "as_refresh_token"

    @property
    def refresh_cookie_samesite(self) -> Literal["lax", "strict", "none"]:
        """First-party cookies on the marketing origin. SameSite=Lax is enough."""
        return self.cookie_samesite

    @property
    def resolved_google_redirect_uri(self) -> str:
        if self.google_redirect_uri and self.google_redirect_uri.strip():
            return self.google_redirect_uri.rstrip("/")
        return f"{self.frontend_url.rstrip('/')}/api/v1/auth/google/callback"

    @property
    def cors_origins(self) -> list[str]:
        origin = self.frontend_url.rstrip("/")
        origins = [origin]
        if origin.startswith("https://www."):
            origins.append(f"https://{origin.removeprefix('https://www.')}")
        elif origin.startswith("https://") and "localhost" not in origin:
            host = origin.removeprefix("https://")
            if not host.startswith("www."):
                origins.append(f"https://www.{host}")
        return origins

    @property
    def google_oauth_configured(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def google_auth_mode(self) -> Literal["live", "mock", "disabled"]:
        if self.google_oauth_configured:
            return "live"
        if self.is_production:
            return "disabled"
        return "mock"

    @field_validator("secret_key")
    @classmethod
    def reject_default_secret_in_production(cls, value: str, info) -> str:
        if value == "changeme-generate-a-secure-random-key":
            environment = info.data.get("environment", "development")
            if environment == "production":
                raise ValueError("SECRET_KEY must be changed in production")
        return value

    @field_validator("cookie_secure", mode="before")
    @classmethod
    def secure_cookies_in_production(cls, value, info) -> bool:
        environment = info.data.get("environment", "development")
        if environment == "production":
            return True
        return bool(value)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
