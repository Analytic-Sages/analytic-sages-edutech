import pytest

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def enable_public_opportunities_hub(monkeypatch):
    """Hub tests describe go-live behavior. Privacy tests turn this off."""
    monkeypatch.setattr(get_settings(), "opportunities_public", True)


@pytest.fixture(autouse=True)
def disable_opportunity_ai_extraction(monkeypatch):
    """Keep the suite hermetic: never call a live LLM or fetch remote pages.

    Opportunity ingestion enriches "thin" listings by fetching the official page
    and calling OpenAI/Gemini. Tests must assert the deterministic parser +
    ingestion behaviour instead, so AI extraction stays off regardless of whether
    developer keys are present in the environment (CI has none).
    """
    monkeypatch.setattr(get_settings(), "opportunity_ai_extraction_enabled", False)


@pytest.fixture(autouse=True)
def disable_classroom_close_loop(monkeypatch):
    """Tests close meetings explicitly; the background loop must stay off."""
    monkeypatch.setattr(get_settings(), "classroom_close_enabled", False)
