from app.core.config import Settings
from app.services.google_oauth import GoogleOAuthService


def test_google_auth_mode_mock_in_development():
    settings = Settings(
        database_url="postgresql://analyticsages:changeme@localhost:5434/analyticsages",
        secret_key="dev-secret-key-for-local-testing-only-32chars",
        environment="development",
        google_client_id=None,
        google_client_secret=None,
    )
    assert settings.google_auth_mode == "mock"


def test_google_oauth_state_roundtrip():
    settings = Settings(
        database_url="postgresql://analyticsages:changeme@localhost:5434/analyticsages",
        secret_key="dev-secret-key-for-local-testing-only-32chars",
        environment="development",
    )
    service = GoogleOAuthService(settings)
    state = service.create_state(next_path="/checkout/python-for-blockchain-analytics")
    payload = service.parse_state(state)
    assert payload["next"] == "/checkout/python-for-blockchain-analytics"
    assert payload["type"] == "google_oauth"
