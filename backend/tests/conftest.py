import pytest

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def enable_public_opportunities_hub(monkeypatch):
    """Hub tests describe go-live behavior. Privacy tests turn this off."""
    monkeypatch.setattr(get_settings(), "opportunities_public", True)
