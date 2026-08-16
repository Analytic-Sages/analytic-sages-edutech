from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.classroom import ClassroomService


def test_list_public_cohorts_returns_active_cards():
    get_settings.cache_clear()
    db = SessionLocal()
    try:
        cards = ClassroomService(db, get_settings()).list_public_cohorts()
        assert isinstance(cards, list)
        for card in cards:
            assert card.status in {"open", "active"}
            assert card.slug
            assert card.name
            assert card.price >= 0
            assert card.currency
    finally:
        db.close()
