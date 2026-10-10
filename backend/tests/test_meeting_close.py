"""End-of-class RealtimeKit close: stop recording and kick everyone out."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.roles import UserRole
from app.db.session import SessionLocal
from app.main import app
from app.models.classroom import (
    Cohort,
    CohortStatus,
    LiveSession,
    LiveSessionStatus,
    LiveSessionType,
)
from app.models.user import User
from app.services.meeting_close import MeetingCloseService, session_should_end
from app.services.realtimekit import RealtimeKitError, RealtimeKitService, recording_ids_to_stop

client = TestClient(app)

COHORT_SLUG = "test-meeting-close-cohort"
EMAIL_PREFIX = "meeting-close-"


def _cleanup() -> None:
    db = SessionLocal()
    try:
        cohort = db.scalar(select(Cohort).where(Cohort.slug == COHORT_SLUG))
        if cohort:
            for row in list(
                db.scalars(select(LiveSession).where(LiveSession.cohort_id == cohort.id)).all()
            ):
                db.delete(row)
            db.delete(cohort)
        for user in list(
            db.scalars(select(User).where(User.email.like(f"{EMAIL_PREFIX}%"))).all()
        ):
            db.delete(user)
        db.commit()
    finally:
        db.close()


def _seed(*, ends_at: datetime, status: LiveSessionStatus = LiveSessionStatus.SCHEDULED) -> uuid.UUID:
    db = SessionLocal()
    try:
        cohort = Cohort(
            id=uuid.uuid4(),
            name="Meeting Close Cohort",
            slug=COHORT_SLUG,
            description="",
            status=CohortStatus.ACTIVE,
            starts_at=datetime.now(UTC) - timedelta(days=1),
        )
        db.add(cohort)
        db.flush()
        session = LiveSession(
            id=uuid.uuid4(),
            cohort_id=cohort.id,
            title="Close me",
            week_label="Week 1",
            session_number=1,
            session_type=LiveSessionType.TEACHING,
            starts_at=ends_at - timedelta(hours=2),
            ends_at=ends_at,
            status=status,
            realtimekit_meeting_id="meeting-to-close",
        )
        db.add(session)
        db.commit()
        return session.id
    finally:
        db.close()


def test_recording_ids_to_stop_ignores_uploaded_files():
    recordings = [
        {"id": "open", "status": "RECORDING"},
        {"id": "invoked", "status": "INVOKED"},
        {"id": "done", "status": "UPLOADED"},
        {"id": "uploading", "status": "UPLOADING"},
        {"status": "RECORDING"},
    ]
    assert recording_ids_to_stop(recordings) == ["open", "invoked"]


def test_session_should_end_only_when_due():
    now = datetime.now(UTC)
    open_row = LiveSession(
        id=uuid.uuid4(),
        cohort_id=uuid.uuid4(),
        title="Open",
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(hours=1),
        status=LiveSessionStatus.SCHEDULED,
        realtimekit_meeting_id="m1",
    )
    assert session_should_end(open_row, now) is False

    past = LiveSession(
        id=uuid.uuid4(),
        cohort_id=uuid.uuid4(),
        title="Past",
        starts_at=now - timedelta(hours=3),
        ends_at=now - timedelta(minutes=1),
        status=LiveSessionStatus.SCHEDULED,
        realtimekit_meeting_id="m2",
    )
    assert session_should_end(past, now) is True

    ended = LiveSession(
        id=uuid.uuid4(),
        cohort_id=uuid.uuid4(),
        title="Ended early",
        starts_at=now - timedelta(minutes=10),
        ends_at=now + timedelta(hours=1),
        status=LiveSessionStatus.ENDED,
        realtimekit_meeting_id="m3",
    )
    assert session_should_end(ended, now) is True

    already = LiveSession(
        id=uuid.uuid4(),
        cohort_id=uuid.uuid4(),
        title="Already closed",
        starts_at=now - timedelta(hours=3),
        ends_at=now - timedelta(minutes=1),
        status=LiveSessionStatus.ENDED,
        realtimekit_meeting_id="m4",
        realtimekit_closed_at=now - timedelta(minutes=1),
    )
    assert session_should_end(already, now) is False


def _kit(*, succeed: bool) -> MagicMock:
    """A configured RealtimeKit stand-in so CI does not skip the close."""
    kit = MagicMock()
    kit.configured = True
    kit.end_live_meeting.return_value = succeed
    kit.find_session_for_meeting.return_value = None
    kit.list_all_session_participants.return_value = []
    return kit


def test_close_elapsed_stops_recording_and_kicks_everyone():
    _cleanup()
    session_id = _seed(ends_at=datetime.now(UTC) - timedelta(minutes=2))
    kit = _kit(succeed=True)

    db = SessionLocal()
    try:
        summary = MeetingCloseService(db, get_settings(), realtimekit=kit).close_elapsed()
        assert summary["failed"] == 0
        row = db.get(LiveSession, session_id)
        assert row is not None
        assert row.realtimekit_closed_at is not None
        assert row.realtimekit_meeting_id == "meeting-to-close"
    finally:
        db.close()

    kit.end_live_meeting.assert_any_call("meeting-to-close")

    kit.reset_mock()
    db = SessionLocal()
    try:
        MeetingCloseService(db, get_settings(), realtimekit=kit).close_elapsed()
        row = db.get(LiveSession, session_id)
        assert row is not None
        assert row.realtimekit_closed_at is not None
    finally:
        db.close()
    assert all(call.args[0] != "meeting-to-close" for call in kit.end_live_meeting.call_args_list)
    _cleanup()


def test_close_elapsed_keeps_room_open_while_instructor_is_present():
    _cleanup()
    session_id = _seed(ends_at=datetime.now(UTC) - timedelta(minutes=2))
    instructor_id = uuid.uuid4()
    kit = _kit(succeed=True)
    kit.find_session_for_meeting.return_value = {
        "id": "provider-session-live",
        "status": "LIVE",
    }
    kit.list_all_session_participants.return_value = [
        {"custom_participant_id": str(instructor_id), "left_at": None}
    ]

    db = SessionLocal()
    try:
        db.add(
            User(
                id=instructor_id,
                email=f"{EMAIL_PREFIX}instructor@example.com",
                full_name="Test Instructor",
                role=UserRole.INSTRUCTOR,
                is_active=True,
            )
        )
        db.commit()

        summary = MeetingCloseService(db, get_settings(), realtimekit=kit).close_elapsed()
        row = db.get(LiveSession, session_id)
        assert summary["failed"] == 0
        assert row is not None
        assert row.realtimekit_closed_at is None
        kit.end_live_meeting.assert_not_called()
    finally:
        db.close()
    _cleanup()


def test_close_elapsed_closes_when_only_students_remain():
    _cleanup()
    session_id = _seed(ends_at=datetime.now(UTC) - timedelta(minutes=2))
    student_id = uuid.uuid4()
    kit = _kit(succeed=True)
    kit.find_session_for_meeting.return_value = {
        "id": "provider-session-live",
        "status": "LIVE",
    }
    kit.list_all_session_participants.return_value = [
        {"custom_participant_id": str(student_id), "left_at": None}
    ]

    db = SessionLocal()
    try:
        db.add(
            User(
                id=student_id,
                email=f"{EMAIL_PREFIX}student@example.com",
                full_name="Test Student",
                role=UserRole.STUDENT,
                is_active=True,
            )
        )
        db.commit()

        MeetingCloseService(db, get_settings(), realtimekit=kit).close_elapsed()
        row = db.get(LiveSession, session_id)
        assert row is not None
        assert row.realtimekit_closed_at is not None
        kit.end_live_meeting.assert_called_once_with("meeting-to-close")
    finally:
        db.close()
    _cleanup()


def test_close_elapsed_fails_open_when_staff_presence_cannot_be_checked():
    _cleanup()
    session_id = _seed(ends_at=datetime.now(UTC) - timedelta(minutes=2))
    kit = _kit(succeed=True)
    kit.find_session_for_meeting.side_effect = RealtimeKitError("provider unavailable")

    db = SessionLocal()
    try:
        summary = MeetingCloseService(db, get_settings(), realtimekit=kit).close_elapsed()
        row = db.get(LiveSession, session_id)
        assert summary["failed"] >= 1
        assert row is not None
        assert row.realtimekit_closed_at is None
        kit.end_live_meeting.assert_not_called()
    finally:
        db.close()
    _cleanup()


def test_explicitly_ended_session_closes_even_if_staff_presence_is_unknown():
    _cleanup()
    session_id = _seed(
        ends_at=datetime.now(UTC) + timedelta(hours=1),
        status=LiveSessionStatus.ENDED,
    )
    kit = _kit(succeed=True)
    kit.find_session_for_meeting.side_effect = RealtimeKitError("should not be called")

    db = SessionLocal()
    try:
        summary = MeetingCloseService(db, get_settings(), realtimekit=kit).close_elapsed()
        row = db.get(LiveSession, session_id)
        assert summary["closed"] >= 1
        assert row is not None
        assert row.realtimekit_closed_at is not None
        kit.find_session_for_meeting.assert_not_called()
        kit.end_live_meeting.assert_called_once_with("meeting-to-close")
    finally:
        db.close()
    _cleanup()


def test_close_elapsed_retries_when_provider_fails():
    _cleanup()
    session_id = _seed(ends_at=datetime.now(UTC) - timedelta(minutes=1))
    kit = _kit(succeed=False)
    db = SessionLocal()
    try:
        summary = MeetingCloseService(db, get_settings(), realtimekit=kit).close_elapsed()
        assert summary["failed"] >= 1
        row = db.get(LiveSession, session_id)
        assert row is not None
        assert row.realtimekit_closed_at is None
    finally:
        db.close()
    kit.end_live_meeting.assert_any_call("meeting-to-close")
    _cleanup()


def test_internal_close_elapsed_is_token_protected(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "classroom_sync_token", "close-token")
    monkeypatch.setattr(settings, "opportunity_sync_token", None)
    monkeypatch.setattr(
        "app.services.meeting_close.RealtimeKitService.end_live_meeting",
        lambda self, meeting_id: True,
    )

    ok = client.post(
        "/api/v1/internal/classroom/close-elapsed",
        headers={"X-Classroom-Sync-Token": "close-token"},
    )
    assert ok.status_code == 200
    assert "closed" in ok.json()

    assert (
        client.post(
            "/api/v1/internal/classroom/close-elapsed",
            headers={"X-Classroom-Sync-Token": "wrong"},
        ).status_code
        == 401
    )

    monkeypatch.setattr(settings, "classroom_sync_token", None)
    assert client.post("/api/v1/internal/classroom/close-elapsed").status_code == 404


def test_end_live_meeting_stops_open_recordings_then_kicks():
    settings = MagicMock()
    settings.cloudflare_account_id = "acct"
    settings.cloudflare_api_token = "token"
    settings.realtimekit_app_id = "app"

    service = RealtimeKitService(settings)
    calls: list[tuple[str, str, dict | None]] = []

    def _fake_get_json(url, *, params=None, attempts=3):
        return {
            "data": {
                "recordings": [
                    {"id": "rec-open", "status": "RECORDING"},
                    {"id": "rec-done", "status": "UPLOADED"},
                ]
            }
        }

    def _fake_mutate(method, url, payload):
        calls.append((method, url, payload))
        return True

    service._get_json = _fake_get_json  # type: ignore[method-assign]
    service._mutate = _fake_mutate  # type: ignore[method-assign]

    assert service.end_live_meeting("meeting-abc") is True
    assert calls[0][0] == "PUT"
    assert "recordings/rec-open" in calls[0][1]
    assert calls[0][2] == {"action": "stop"}
    assert calls[1][0] == "POST"
    assert calls[1][1].endswith("/meetings/meeting-abc/active-session/kick-all")
    assert len(calls) == 2
