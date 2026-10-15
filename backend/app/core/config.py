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
    # Seconds to wait for the Postgres TCP/startup handshake before giving up.
    # Without this psycopg2 blocks indefinitely when the database is unreachable.
    database_connect_timeout_seconds: int = 10

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
    # Comma-separated admin emails allowed to view and message event registrants.
    event_registrant_manager_emails: str | None = None
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

    # Safety net for missed/late NOWPayments IPNs. A background sweep pulls the
    # real status for stale pending payments so a student unlocks their seat even
    # if they closed the checkout tab before the crypto settled. Also exposed via
    # POST /api/v1/internal/payments/reconcile (token header) for cron/ops.
    payments_reconcile_enabled: bool = True
    payments_reconcile_interval_seconds: int = 300
    payments_reconcile_batch_limit: int = 25
    payments_reconcile_token: str | None = None

    # Cloudflare RealtimeKit (live classroom) — leave empty for mock join mode
    cloudflare_account_id: str | None = None
    cloudflare_api_token: str | None = None
    realtimekit_app_id: str | None = None
    realtimekit_host_preset: str = "group_call_host"
    realtimekit_participant_preset: str = "group_call_participant"
    # Ask RealtimeKit to record the meeting as soon as it starts, so ended sessions
    # can sync their recording URL automatically. Requires recording enabled on the
    # Cloudflare account.
    realtimekit_record_on_start: bool = True
    # When a class passes ends_at (or is marked ended/cancelled), kick the live
    # room and stop the recording even if every browser has already disconnected.
    classroom_close_enabled: bool = True
    classroom_close_interval_seconds: int = 15
    # Shared secret for POST /api/v1/webhooks/realtimekit. Unsigned calls are rejected.
    realtimekit_webhook_secret: str | None = None

    # Cloudflare R2 (S3-compatible) private archive for live-session recordings.
    # Credentials stay server-side. The bucket must not be public.
    # Endpoint defaults to https://<CLOUDFLARE_ACCOUNT_ID>.r2.cloudflarestorage.com.
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket: str = "analytic-sages-recordings"
    r2_recording_prefix: str = "live-sessions/"
    r2_endpoint_url: str | None = None

    # RealtimeKit attendance sync — post-session reconciliation of participant
    # join/leave intervals into the LMS attendance records. Off by default so
    # nothing changes until enabled; the internal endpoint + admin action still work.
    attendance_sync_enabled: bool = False
    attendance_sync_interval_seconds: int = 1800
    # Default attendance rules (per-cohort overrides live in
    # cohorts.enrollment_settings["attendance"]). A student is Present when their
    # non-overlapping attended time meets BOTH the minimum seconds and the minimum
    # percentage of the scheduled session length.
    attendance_default_min_seconds: int = 600
    attendance_default_min_percent: float = 30.0
    attendance_late_grace_minutes: int = 10

    # Local article image uploads (dev / API disk). Not Postgres.
    # Falls back to this when Supabase Storage is not configured — not durable across deploys.
    storage_dir: str = "var/uploads"

    # Supabase Storage — durable object storage for Insights/Events image uploads.
    # Leave empty to use local disk (dev only).
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_storage_bucket: str = "uploads"

    # Cloudflare Stream (VOD for self-paced lessons) — reuses the Cloudflare account
    # + API token used by RealtimeKit. Leave empty to keep lessons YouTube-only /
    # mock uploads. CLOUDFLARE_STREAM_CUSTOMER_CODE is the `customer-xxxx` subdomain
    # from the Stream dashboard, used to build playback/embed/thumbnail URLs.
    cloudflare_stream_customer_code: str | None = None
    cloudflare_stream_default_max_duration_seconds: int = 21600  # 6h ceiling for uploads
    # Optional Stream signing key (id + RSA private key PEM) for private playback.
    # When set, recordings use requireSignedURLs and the API mints short-lived tokens.
    cloudflare_stream_signing_key_id: str | None = None
    cloudflare_stream_signing_key_pem: str | None = None

    # Certifier.io certificates. Leave CERTIFIER_API_KEY empty for mock/log-only mode.
    certifier_api_key: str | None = None
    certifier_api_url: str = "https://api.certifier.io/v1"
    certifier_version: str = "2022-10-26"
    # Fallback Certifier group when a course has no certifier_group_id set.
    certifier_group_id: str | None = None
    # Optional shared secret for POST /api/v1/webhooks/certifier signature checks.
    certifier_webhook_secret: str | None = None

    # Feature gates — all default off so nothing changes in production until enabled.
    certificates_enabled: bool = False
    quizzes_enabled: bool = False
    assignments_enabled: bool = False
    notifications_enabled: bool = False
    course_authoring_enabled: bool = False

    # Installment payment reminders (due-soon / on-due / overdue emails).
    billing_reminders_enabled: bool = False
    billing_reminders_interval_seconds: int = 3600
    billing_reminder_lead_days: int = 3
    billing_reminders_token: str | None = None

    # Optional header token for POST /api/v1/internal/opportunities/sync and weekly digest.
    # Leave empty to keep the endpoints disabled.
    opportunity_sync_token: str | None = None

    # Optional header token for POST /api/v1/internal/classroom/sync-schedule.
    # Re-provisions the canonical Blockchain Data Engineering 30-session schedule in
    # any environment (idempotent). Falls back to OPPORTUNITY_SYNC_TOKEN when unset.
    classroom_sync_token: str | None = None

    # Public opportunities hub. Off until go-live so listings stay staff-only.
    opportunities_public: bool = False

    # Public Referral Partner programme (/partners). Off until go-live; admins still manage referrals.
    partners_public: bool = False

    # Cohort tuition plans / installments. Off keeps legacy one-time checkout.
    billing_plans_enabled: bool = False

    # Referral Partner Program (learner course/programme referrals — not opportunities staff)
    default_referral_commission_rate: str = "0.07"
    referral_attribution_days: int = 30
    commission_hold_days: int = 14
    # Legacy single-currency fallback when MINIMUM_PAYOUT_THRESHOLDS_JSON is unset
    minimum_payout_amount: str = "10000"
    minimum_payout_currency: str = "NGN"
    # USD-first reporting (informational only — does not rewrite ledger currency)
    reporting_base_currency: str = "USD"
    default_global_minimum_payout_usd_equivalent: str = "25"
    # JSON map e.g. {"USD":"25","USDT":"25","NGN":"40000"} — empty derives from USD equiv + FX
    minimum_payout_thresholds_json: str | None = None
    # JSON map of USD per 1 unit e.g. {"USD":"1","NGN":"0.000625"} — empty uses Paystack NGN rate
    referral_reporting_fx_rates_json: str | None = None
    referral_default_redirect_path: str = "/programs"
    # Optional header token for POST /api/v1/internal/referrals/release-commissions
    referral_release_token: str | None = None

    # Telegram Bot API. Leave empty to skip announcements on publish.
    telegram_bot_token: str | None = None
    telegram_channel_id: str | None = None

    # Optional LLM review assist and typed discovery. Never auto-publishes.
    # OpenAI is tried first; Gemini is the fallback when OpenAI is missing or fails.
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    # When true and an LLM key is set: fetch original pages and extract missing fields.
    opportunity_ai_extraction_enabled: bool = True
    opportunity_ai_extraction_max_chars: int = 12000

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
    def certifier_configured(self) -> bool:
        return bool(self.certifier_api_key)

    @property
    def cloudflare_stream_configured(self) -> bool:
        return bool(
            self.cloudflare_account_id
            and self.cloudflare_api_token
            and self.cloudflare_stream_customer_code
        )

    @property
    def resolved_r2_endpoint(self) -> str | None:
        if self.r2_endpoint_url and self.r2_endpoint_url.strip():
            return self.r2_endpoint_url.strip().rstrip("/")
        if self.cloudflare_account_id:
            return f"https://{self.cloudflare_account_id.strip()}.r2.cloudflarestorage.com"
        return None

    @property
    def r2_configured(self) -> bool:
        return bool(
            self.r2_access_key_id
            and self.r2_secret_access_key
            and self.r2_bucket.strip()
            and self.resolved_r2_endpoint
        )

    @property
    def r2_recording_prefix_normalized(self) -> str:
        prefix = (self.r2_recording_prefix or "live-sessions").strip().strip("/")
        if not prefix or ".." in prefix.split("/"):
            return "live-sessions"
        return prefix

    @property
    def cloudflare_stream_signing_configured(self) -> bool:
        """Signed (private) playback is available when a signing key is configured."""
        return bool(
            self.cloudflare_stream_signing_key_id and self.cloudflare_stream_signing_key_pem
        )

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

    @field_validator("database_url", mode="before")
    @classmethod
    def pin_psycopg2_driver(cls, value: str) -> str:
        """Force psycopg2 (the only driver we install) instead of SQLAlchemy's default resolution."""
        if isinstance(value, str) and "+" not in value.split("://", 1)[0]:
            scheme, _, rest = value.partition("://")
            if scheme in {"postgres", "postgresql"}:
                return f"postgresql+psycopg2://{rest}"
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
