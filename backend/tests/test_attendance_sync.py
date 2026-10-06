"""RealtimeKit attendance reconciliation tests.

All provider responses are mocked — no real Cloudflare meeting is required.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.live import AttendanceStatus
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.attendance import Attendance, AttendanceInterval, AttendanceParticipant
from app.models.classroom import (
    Cohort,
    CohortMember,
    CohortMemberRole,
    CohortStatus,
    LiveSession,
    LiveSessionStatus,
    LiveSessionType,
    SessionRecording,
)
from app.models.user import User
from app.services.attendance import AttendanceSyncService
from app.services.realtimekit import RealtimeKitError, RealtimeKitService

client = TestClient(app)

COHORT_SLUG = "test-attendance-sync-cohort"
EMAIL_PREFIX = "attendance-test-"
MEETING_ID = "meeting-attendance-1"
PROVIDER_SESSION_ID = "prov-session-1"


# ---------- provider mocking ----------


def _install_provider(
    monkeypatch,
    *,
    provider_session,
    participants=None,
    sessions_error=None,
    participants_error=None,
    fail_times=1,
):
    """Patch the RealtimeKit client so no network call is made."""
    state = {"calls": 0}

    def fake_find(self, meeting_id):  # noqa: ANN001
        state["calls"] += 1
        if sessions_error is not None and state["calls"] <= fail_times:
            raise sessions_error
        return provider_session

    def fake_participants(self, session_id, include_peer_events=True, max_pages=20):  # noqa: ANN001
        if participants_error is not None:
            raise participants_error
        return list(participants or [])

    monkeypatch.setattr(RealtimeKitService, "find_session_for_meeting", fake_find)
    monkeypatch.setattr(RealtimeKitService, "list_all_session_participants", fake_participants)


def _provider_session(*, status="ENDED", ended=True, meeting_id=MEETING_ID):
    starts = datetime.now(UTC) - timedelta(hours=3)
    ends = datetime.now(UTC) - timedelta(hours=2)
    return {
        "id": PROVIDER_SESSION_ID,
        "associated_id": meeting_id,
        "status": status,
        "started_at": starts.isoformat(),
        "ended_at": ends.isoformat() if ended else None,
    }


def _participant(
    pid: str,
    *,
    user_id=None,
    name="Participant",
    joined=None,
    left=None,
    duration=None,
    peer_events=None,
):
    raw: dict = {"id": pid, "display_name": name}
    if user_id is not None:
        raw["custom_participant_id"] = str(user_id)
    if joined is not None:
        raw["joined_at"] = joined.isoformat()
    if left is not None:
        raw["left_at"] = left.isoformat()
    if duration is not None:
        raw["duration"] = duration
    if peer_events is not None:
        raw["peer_events"] = peer_events
    return raw


def _token_for(user: User) -> str:
    return SecurityService(get_settings()).create_access_token(
        user_id=str(user.id), role=user.role.value
    )


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_for(user)}"}


def _make_user(prefix: str, role: UserRole = UserRole.STUDENT) -> User:
    db = SessionLocal()
    db.expire_on_commit = False
    try:
        user = User(
            email=f"{EMAIL_PREFIX}{prefix}-{uuid.uuid4().hex[:8]}@example.com",
            full_name=f"Attendance {prefix}",
            role=role,
            email_verified=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def _cleanup() -> None:
    db = SessionLocal()
    try:
        cohort = db.scalar(select(Cohort).where(Cohort.slug == COHORT_SLUG))
        if cohort:
            session_ids = [
                s.id
                for s in db.scalars(
                    select(LiveSession).where(LiveSession.cohort_id == cohort.id)
                ).all()
            ]
            if session_ids:
                for rec in db.scalars(
                    select(SessionRecording).where(SessionRecording.session_id.in_(session_ids))
                ).all():
                    db.delete(rec)
                for part in db.scalars(
                    select(AttendanceParticipant).where(
                        AttendanceParticipant.session_id.in_(session_ids)
                    )
                ).all():
                    db.delete(part)
                for row in db.scalars(
                    select(Attendance).where(Attendance.session_id.in_(session_ids))
                ).all():
                    db.delete(row)
            for session in db.scalars(
                select(LiveSession).where(LiveSession.cohort_id == cohort.id)
            ).all():
                db.delete(session)
            for member in db.scalars(
                select(CohortMember).where(CohortMember.cohort_id == cohort.id)
            ).all():
                db.delete(member)
            db.delete(cohort)
        for user in db.scalars(
            select(User).where(User.email.like(f"{EMAIL_PREFIX}%"))
        ).all():
            db.delete(user)
        db.commit()
    finally:
        db.close()


def _seed(*, session_status=LiveSessionStatus.ENDED, meeting_id=MEETING_ID):
    """Seed a cohort with two enrolled students and one session."""
    _cleanup()
    db = SessionLocal()
    db.expire_on_commit = False
    try:
        cohort = Cohort(
            id=uuid.uuid4(),
            name="Attendance Sync Cohort",
            slug=COHORT_SLUG,
            description="",
            status=CohortStatus.ACTIVE,
            starts_at=datetime.now(UTC) - timedelta(days=1),
        )
        db.add(cohort)
        db.flush()

        students = []
        for label in ("alpha", "beta"):
            user = User(
                email=f"{EMAIL_PREFIX}{label}-{uuid.uuid4().hex[:8]}@example.com",
                full_name=f"Attendance {label}",
                role=UserRole.STUDENT,
                email_verified=True,
                is_active=True,
            )
            db.add(user)
            db.flush()
            students.append(user)

        session = LiveSession(
            id=uuid.uuid4(),
            cohort_id=cohort.id,
            title="Attendance session",
            week_label="Week 1",
            session_number=1,
            session_type=LiveSessionType.TEACHING,
            starts_at=datetime.now(UTC) - timedelta(hours=2),
            ends_at=datetime.now(UTC) - timedelta(hours=1),
            status=session_status,
            realtimekit_meeting_id=meeting_id,
        )
        db.add(session)
        db.flush()

        for user in students:
            db.add(
                CohortMember(cohort_id=cohort.id, user_id=user.id, role=CohortMemberRole.STUDENT)
            )
        db.commit()
        return cohort.id, session.id, students[0], students[1]
    finally:
        db.close()


def _attendance_for(session_id, user_id):
    db = SessionLocal()
    try:
        return db.scalar(
            select(Attendance).where(
                Attendance.session_id == session_id, Attendance.user_id == user_id
            )
        )
    finally:
        db.close()


def _sync(session_id):
    db = SessionLocal()
    try:
        service = AttendanceSyncService(db, get_settings())
        session = db.get(LiveSession, session_id)
        return service.sync_session(session)
    finally:
        db.close()


def _session_times(session_id):
    db = SessionLocal()
    try:
        session = db.get(LiveSession, session_id)
        return session.starts_at, session.ends_at
    finally:
        db.close()


# ---------- Phase 8: attendance matrix ----------


def test_full_attendance_is_marked_attended(monkeypatch):
    _, session_id, student_a, student_b = _seed()
    starts, ends = _session_times(session_id)
    _install_provider(
        monkeypatch,
        provider_session=_provider_session(),
        participants=[_participant("p1", user_id=student_a.id, joined=starts, left=ends)],
    )

    result = _sync(session_id)
    assert result.status == "ok"
    assert result.matched == 1

    row = _attendance_for(session_id, student_a.id)
    assert row.status == AttendanceStatus.ATTENDED
    assert row.total_attendance_seconds == 3600
    assert row.provider == "realtimekit"
    # The enrolled student who never joined is marked absent once finalized.
    assert _attendance_for(session_id, student_b.id).status == AttendanceStatus.ABSENT
    _cleanup()


def test_late_arrival_is_marked_late(monkeypatch):
    _, session_id, student_a, _ = _seed()
    starts, ends = _session_times(session_id)
    _install_provider(
        monkeypatch,
        provider_session=_provider_session(),
        participants=[
            _participant("p1", user_id=student_a.id, joined=starts + timedelta(minutes=30), left=ends)
        ],
    )
    assert _sync(session_id).status == "ok"
    assert _attendance_for(session_id, student_a.id).status == AttendanceStatus.LATE
    _cleanup()


def test_early_departure_below_threshold_is_late(monkeypatch):
    _, session_id, student_a, _ = _seed()
    starts, _ = _session_times(session_id)
    _install_provider(
        monkeypatch,
        provider_session=_provider_session(),
        participants=[
            _participant("p1", user_id=student_a.id, joined=starts, left=starts + timedelta(minutes=10))
        ],
    )
    assert _sync(session_id).status == "ok"
    row = _attendance_for(session_id, student_a.id)
    assert row.status == AttendanceStatus.LATE
    assert row.total_attendance_seconds == 600
    _cleanup()


def test_leaving_and_rejoining_sums_intervals(monkeypatch):
    _, session_id, student_a, _ = _seed()
    starts, _ = _session_times(session_id)
    events = [
        {"id": "e1", "event_name": "PEER_JOINING", "created_at": starts.isoformat()},
        {
            "id": "e2",
            "event_name": "PEER_LEAVING",
            "created_at": (starts + timedelta(minutes=10)).isoformat(),
        },
        {
            "id": "e3",
            "event_name": "PEER_JOINING",
            "created_at": (starts + timedelta(minutes=20)).isoformat(),
        },
        {
            "id": "e4",
            "event_name": "PEER_LEAVING",
            "created_at": (starts + timedelta(minutes=40)).isoformat(),
        },
    ]
    _install_provider(
        monkeypatch,
        provider_session=_provider_session(),
        participants=[
            _participant(
                "p1",
                user_id=student_a.id,
                joined=starts,
                left=starts + timedelta(minutes=40),
                peer_events=events,
            )
        ],
    )
    assert _sync(session_id).status == "ok"
    row = _attendance_for(session_id, student_a.id)
    assert row.total_attendance_seconds == 1800  # 10m + 20m, non-overlapping

    db = SessionLocal()
    try:
        part = db.scalar(
            select(AttendanceParticipant).where(AttendanceParticipant.session_id == session_id)
        )
        intervals = db.scalars(
            select(AttendanceInterval).where(AttendanceInterval.participant_id == part.id)
        ).all()
        assert len(intervals) == 2
    finally:
        db.close()
    _cleanup()


def test_duplicate_sync_is_idempotent(monkeypatch):
    _, session_id, student_a, _ = _seed()
    starts, ends = _session_times(session_id)
    _install_provider(
        monkeypatch,
        provider_session=_provider_session(),
        participants=[_participant("p1", user_id=student_a.id, joined=starts, left=ends)],
    )
    _sync(session_id)
    _sync(session_id)

    db = SessionLocal()
    try:
        parts = db.scalars(
            select(AttendanceParticipant).where(AttendanceParticipant.session_id == session_id)
        ).all()
        rows = db.scalars(
            select(Attendance).where(Attendance.session_id == session_id)
        ).all()
    finally:
        db.close()
    assert len(parts) == 1
    # one present + one absent (the non-joining student), never duplicated
    assert len(rows) == 2
    _cleanup()


def test_unknown_participant_is_flagged_not_guessed(monkeypatch):
    _, session_id, _, _ = _seed()
    starts, ends = _session_times(session_id)
    _install_provider(
        monkeypatch,
        provider_session=_provider_session(),
        participants=[_participant("ghost", name="Jane Doe", joined=starts, left=ends)],
    )
    result = _sync(session_id)
    assert result.status == "needs_review"
    assert result.unmatched == 1
    assert result.matched == 0

    db = SessionLocal()
    try:
        part = db.scalar(
            select(AttendanceParticipant).where(AttendanceParticipant.session_id == session_id)
        )
    finally:
        db.close()
    assert part.user_id is None
    assert part.sync_status.value == "needs_review"

    # No attendance row is invented for the unknown participant: only the two
    # enrolled students get a row (both absent, since neither was present).
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(Attendance).where(Attendance.session_id == session_id)
        ).all()
    finally:
        db.close()
    assert len(rows) == 2
    assert all(r.status == AttendanceStatus.ABSENT for r in rows)
    _cleanup()
def test_missing_provider_data_is_pending_not_absent(monkeypatch):
    _, session_id, student_a, student_b = _seed()
    _install_provider(monkeypatch, provider_session=None, participants=[])

    result = _sync(session_id)
    assert result.status == "pending"
    # Nothing is finalized yet — no student is marked absent.
    assert _attendance_for(session_id, student_a.id) is None
    assert _attendance_for(session_id, student_b.id) is None
    _cleanup()


def test_provider_api_failure_marks_error_then_retry_succeeds(monkeypatch):
    _, session_id, student_a, _ = _seed()
    starts, ends = _session_times(session_id)

    _install_provider(
        monkeypatch,
        provider_session=_provider_session(),
        sessions_error=RealtimeKitError("provider down", status_code=503),
        fail_times=1,
    )
    first = _sync(session_id)
    assert first.status == "error"
    assert _attendance_for(session_id, student_a.id) is None

    # A later retry (same provider now healthy) reconciles successfully.
    _install_provider(
        monkeypatch,
        provider_session=_provider_session(),
        participants=[_participant("p1", user_id=student_a.id, joined=starts, left=ends)],
    )
    second = _sync(session_id)
    assert second.status == "ok"
    assert _attendance_for(session_id, student_a.id).status == AttendanceStatus.ATTENDED
    _cleanup()


def test_in_progress_session_never_marks_absent(monkeypatch):
    _, session_id, student_a, student_b = _seed(session_status=LiveSessionStatus.LIVE)
    starts, _ = _session_times(session_id)
    _install_provider(
        monkeypatch,
        provider_session=_provider_session(status="LIVE", ended=False),
        # Joined but has not left yet → no confident duration.
        participants=[_participant("p1", user_id=student_a.id, joined=starts)],
    )
    result = _sync(session_id)
    assert result.status == "pending"
    assert _attendance_for(session_id, student_a.id) is None
    assert _attendance_for(session_id, student_b.id) is None
    _cleanup()


def test_manual_correction_survives_subsequent_sync(monkeypatch):
    _, session_id, student_a, _ = _seed()
    starts, ends = _session_times(session_id)

    db = SessionLocal()
    try:
        db.add(
            Attendance(
                id=uuid.uuid4(),
                session_id=session_id,
                user_id=student_a.id,
                status=AttendanceStatus.ABSENT,
                manual_override=True,
                override_reason="Instructor confirmed the student did not attend.",
            )
        )
        db.commit()
    finally:
        db.close()

    _install_provider(
        monkeypatch,
        provider_session=_provider_session(),
        participants=[_participant("p1", user_id=student_a.id, joined=starts, left=ends)],
    )
    assert _sync(session_id).status == "ok"

    row = _attendance_for(session_id, student_a.id)
    assert row.status == AttendanceStatus.ABSENT  # override preserved
    assert row.manual_override is True
    assert row.last_synced_at is not None
    _cleanup()
def test_resolve_participant_creates_manual_override(monkeypatch):
    _, session_id, _, student_b = _seed()
    starts, ends = _session_times(session_id)
    _install_provider(
        monkeypatch,
        provider_session=_provider_session(),
        participants=[_participant("ghost", name="Jane Doe", joined=starts, left=ends)],
    )
    _sync(session_id)

    ops = _make_user("ops-resolve", UserRole.OPERATIONS)
    db = SessionLocal()
    try:
        part = db.scalar(
            select(AttendanceParticipant).where(AttendanceParticipant.session_id == session_id)
        )
        part_id = part.id
    finally:
        db.close()

    resp = client.post(
        f"/api/v1/admin/attendance-participants/{part_id}/resolve",
        headers=_auth(ops),
        json={"user_id": str(student_b.id), "status": "attended", "reason": "ID checked"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["matched"] is True

    row = _attendance_for(session_id, student_b.id)
    assert row.status == AttendanceStatus.ATTENDED
    assert row.manual_override is True
    assert row.overridden_by == ops.id

    # Re-syncing keeps the human resolution intact.
    _sync(session_id)
    row = _attendance_for(session_id, student_b.id)
    assert row.manual_override is True
    assert row.status == AttendanceStatus.ATTENDED
    _cleanup()


def test_unauthorized_user_cannot_trigger_sync(monkeypatch):
    _, session_id, _, _ = _seed()
    editor = _make_user("editor-no", UserRole.EDITOR)
    student = _make_user("student-no", UserRole.STUDENT)

    for user in (editor, student):
        resp = client.post(
            f"/api/v1/admin/classroom/sessions/{session_id}/sync-attendance",
            headers=_auth(user),
        )
        assert resp.status_code == 403
    _cleanup()


def test_operations_and_admin_can_sync_and_read(monkeypatch):
    _, session_id, student_a, _ = _seed()
    starts, ends = _session_times(session_id)
    _install_provider(
        monkeypatch,
        provider_session=_provider_session(),
        participants=[_participant("p1", user_id=student_a.id, joined=starts, left=ends)],
    )
    ops = _make_user("ops-sync", UserRole.OPERATIONS)

    sync_resp = client.post(
        f"/api/v1/admin/classroom/sessions/{session_id}/sync-attendance",
        headers=_auth(ops),
    )
    assert sync_resp.status_code == 200, sync_resp.text
    assert sync_resp.json()["status"] == "ok"

    detail = client.get(
        f"/api/v1/admin/classroom/sessions/{session_id}/attendance", headers=_auth(ops)
    )
    assert detail.status_code == 200
    body = detail.json()
    assert body["matched_count"] == 1
    assert body["unmatched_count"] == 0
    assert any(s["status"] == "attended" for s in body["expected_students"])
    _cleanup()


def test_internal_sync_attendance_is_token_protected(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "classroom_sync_token", "attendance-token")
    monkeypatch.setattr(settings, "opportunity_sync_token", None)

    ok = client.post(
        "/api/v1/internal/classroom/sync-attendance",
        headers={"X-Classroom-Sync-Token": "attendance-token"},
    )
    assert ok.status_code == 200
    assert "total" in ok.json()

    assert (
        client.post(
            "/api/v1/internal/classroom/sync-attendance",
            headers={"X-Classroom-Sync-Token": "wrong"},
        ).status_code
        == 401
    )

    monkeypatch.setattr(settings, "classroom_sync_token", None)
    assert client.post("/api/v1/internal/classroom/sync-attendance").status_code == 404
def test_attendance_and_recording_sync_are_independent(monkeypatch):
    from app.services.recordings import RecordingsService

    cohort_id, session_id, student_a, _ = _seed()
    starts, ends = _session_times(session_id)
    settings = get_settings()

    # (1) Attendance succeeds while the recording hand-off fails.
    _install_provider(
        monkeypatch,
        provider_session=_provider_session(),
        participants=[_participant("p1", user_id=student_a.id, joined=starts, left=ends)],
    )

    def _boom(self, *, meeting_id):
        raise RealtimeKitError("recording boom")

    monkeypatch.setattr(RealtimeKitService, "latest_download_url", _boom)
    db = SessionLocal()
    try:
        recordings = RecordingsService(db, settings).sync_all(cohort_id=cohort_id)
    finally:
        db.rollback()
        db.close()
    assert recordings["failed"] >= 1

    db = SessionLocal()
    try:
        attendance = AttendanceSyncService(db, settings).sync_all(cohort_id=cohort_id)
    finally:
        db.close()
    assert attendance.updated >= 1
    assert attendance.failed == 0

    # (2) Recording sync succeeds (no recording yet → still processing) while
    #     attendance fails.
    monkeypatch.setattr(
        RealtimeKitService, "latest_download_url", lambda self, *, meeting_id: None
    )
    _install_provider(
        monkeypatch,
        provider_session=_provider_session(),
        sessions_error=RealtimeKitError("attendance boom"),
        fail_times=999,
    )

    db = SessionLocal()
    try:
        recordings = RecordingsService(db, settings).sync_all(cohort_id=cohort_id)
    finally:
        db.close()
    assert recordings["failed"] == 0

    db = SessionLocal()
    try:
        attendance = AttendanceSyncService(db, settings).sync_all(cohort_id=cohort_id)
    finally:
        db.rollback()
        db.close()
    assert attendance.failed >= 1
    _cleanup()


def test_realtimekit_client_retries_transient_failures(monkeypatch):
    """The Sessions API client retries 5xx responses with backoff."""
    import app.services.realtimekit as rk_module
    from app.core.config import Settings

    settings = Settings(
        database_url="postgresql://u:p@localhost:5432/db",
        secret_key="x" * 32,
        cloudflare_account_id="acct",
        cloudflare_api_token="token",
        realtimekit_app_id="app",
    )
    service = RealtimeKitService(settings)

    attempts = {"count": 0}

    class FakeResponse:
        def __init__(self, status_code, payload=None):
            self.status_code = status_code
            self._payload = payload or {}
            self.text = "err"

        def json(self):
            return self._payload

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, headers=None, params=None):
            attempts["count"] += 1
            if attempts["count"] < 3:
                return FakeResponse(503)
            return FakeResponse(200, {"data": {"sessions": [{"id": "s1"}]}})

    monkeypatch.setattr(rk_module.httpx, "Client", FakeClient)
    monkeypatch.setattr(rk_module.time, "sleep", lambda *_: None)

    result = service.list_sessions(associated_id="m1")
    assert attempts["count"] == 3
    assert result["sessions"] == [{"id": "s1"}]
# ---------- db fixtures ----------