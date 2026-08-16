from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from app.core.config import Settings
from app.models.classroom import Cohort, LiveSession, LiveSessionStatus
from app.services.classroom import EARLY_JOIN_MINUTES, ClassroomService


def _service() -> ClassroomService:
    settings = MagicMock(spec=Settings)
    settings.realtimekit_host_preset = "webinar_host"
    settings.realtimekit_participant_preset = "webinar_participant"
    return ClassroomService(MagicMock(), settings)


def test_phase_upcoming_before_early_join_window():
    now = datetime.now(timezone.utc)
    session = LiveSession(
        id=uuid4(),
        cohort_id=uuid4(),
        title="Upcoming",
        starts_at=now + timedelta(minutes=EARLY_JOIN_MINUTES + 10),
        ends_at=now + timedelta(hours=2),
        status=LiveSessionStatus.SCHEDULED,
    )
    assert _service()._effective_phase(session) == "upcoming"


def test_phase_live_inside_early_join_window():
    now = datetime.now(timezone.utc)
    session = LiveSession(
        id=uuid4(),
        cohort_id=uuid4(),
        title="Almost live",
        starts_at=now + timedelta(minutes=5),
        ends_at=now + timedelta(hours=2),
        status=LiveSessionStatus.SCHEDULED,
    )
    assert _service()._effective_phase(session) == "live"


def test_phase_ended_after_ends_at():
    now = datetime.now(timezone.utc)
    session = LiveSession(
        id=uuid4(),
        cohort_id=uuid4(),
        title="Past",
        starts_at=now - timedelta(hours=3),
        ends_at=now - timedelta(minutes=5),
        status=LiveSessionStatus.SCHEDULED,
    )
    assert _service()._effective_phase(session) == "ended"


def test_phase_respects_cancelled_status():
    now = datetime.now(timezone.utc)
    session = LiveSession(
        id=uuid4(),
        cohort_id=uuid4(),
        title="Cancelled",
        starts_at=now - timedelta(minutes=5),
        ends_at=now + timedelta(hours=1),
        status=LiveSessionStatus.CANCELLED,
    )
    assert _service()._effective_phase(session) == "cancelled"


def test_cohort_slug_constant_usable():
    cohort = Cohort(
        id=uuid4(),
        name="Cohort 9",
        slug="cohort-9",
        description="",
    )
    assert cohort.slug == "cohort-9"
