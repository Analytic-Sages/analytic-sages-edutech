from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.classroom import (
    Cohort,
    CohortMember,
    CohortMemberRole,
    CohortStatus,
    LiveSession,
    LiveSessionStatus,
    LiveSessionType,
    RecordingStatus,
    SessionRecording,
)
from app.models.user import User

client = TestClient(app)

COHORT_SLUG = "test-recordings-cohort"


def _token_for(user: User) -> str:
    return SecurityService(get_settings()).create_access_token(
        user_id=str(user.id), role=user.role.value
    )


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_for(user)}"}


def _make_user(prefix: str, role: UserRole = UserRole.STUDENT) -> User:
    db = SessionLocal()
    try:
        user = User(
            email=f"{prefix}-{uuid.uuid4().hex[:8]}@example.com",
            full_name="Recordings Test",
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
            for session in db.scalars(
                select(LiveSession).where(LiveSession.cohort_id == cohort.id)
            ).all():
                db.delete(session)
            for member in db.scalars(
                select(CohortMember).where(CohortMember.cohort_id == cohort.id)
            ).all():
                db.delete(member)
            db.delete(cohort)
        for user in db.scalars(select(User).where(User.email.like("%recordings-test-%@example.com"))).all():
            db.delete(user)
        db.commit()
    finally:
        db.close()


def _seed() -> tuple[uuid.UUID, uuid.UUID]:
    """Seed a cohort + one ended session + a READY recording. Returns ids."""
    db = SessionLocal()
    try:
        cohort = Cohort(
            id=uuid.uuid4(),
            name="Recordings Test Cohort",
            slug=COHORT_SLUG,
            description="",
            status=CohortStatus.OPEN,
            starts_at=datetime.now(UTC) - timedelta(days=7),
        )
        db.add(cohort)
        db.flush()
        session = LiveSession(
            id=uuid.uuid4(),
            cohort_id=cohort.id,
            title="Recorded session",
            week_label="Week 1",
            session_number=1,
            session_type=LiveSessionType.TEACHING,
            starts_at=datetime.now(UTC) - timedelta(days=1),
            ends_at=datetime.now(UTC) - timedelta(hours=22),
            status=LiveSessionStatus.ENDED,
        )
        db.add(session)
        db.flush()
        db.add(
            SessionRecording(
                id=uuid.uuid4(),
                session_id=session.id,
                provider="cloudflare_stream",
                provider_recording_id="stream-uid-xyz",
                status=RecordingStatus.READY,
                storage_provider="cloudflare_stream",
                storage_key="stream-uid-xyz",
                recording_url="https://customer-test.cloudflarestream.com/stream-uid-xyz/iframe",
                duration_seconds=3600,
            )
        )
        db.commit()
        return cohort.id, session.id
    finally:
        db.close()


def test_enrolled_student_can_watch_ready_recording():
    _cleanup()
    cohort_id, session_id = _seed()
    student = _make_user("recordings-test-student")
    db = SessionLocal()
    try:
        db.add(
            CohortMember(cohort_id=cohort_id, user_id=student.id, role=CohortMemberRole.STUDENT)
        )
        db.commit()
    finally:
        db.close()

    resp = client.get(
        f"/api/v1/cohorts/{cohort_id}/sessions/{session_id}/recording",
        headers=_auth(student),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "ready"
    # A signed/gated playback URL is minted per request (never the expiring R2 URL).
    assert body["watch_url"]
    assert body["duration_seconds"] == 3600
    _cleanup()


def test_non_enrolled_user_cannot_access_recording():
    _cleanup()
    cohort_id, session_id = _seed()
    stranger = _make_user("recordings-test-stranger")
    resp = client.get(
        f"/api/v1/cohorts/{cohort_id}/sessions/{session_id}/recording",
        headers=_auth(stranger),
    )
    assert resp.status_code == 403
    _cleanup()


def test_operations_can_preview_recording_but_editor_cannot():
    _cleanup()
    cohort_id, session_id = _seed()
    ops = _make_user("recordings-test-ops", UserRole.OPERATIONS)
    editor = _make_user("recordings-test-editor", UserRole.EDITOR)

    ops_resp = client.get(
        f"/api/v1/cohorts/{cohort_id}/sessions/{session_id}/recording",
        headers=_auth(ops),
    )
    assert ops_resp.status_code == 200

    editor_resp = client.get(
        f"/api/v1/cohorts/{cohort_id}/sessions/{session_id}/recording",
        headers=_auth(editor),
    )
    assert editor_resp.status_code == 403
    _cleanup()


def test_watch_uses_private_r2_when_stream_url_is_missing():
    """A ready Stream row with no playable URL falls back to the R2 archive."""
    _cleanup()
    cohort_id, session_id = _seed()
    recording_id = "fff4d97c-b29d-4a88-8fb6-0d46e13ee11c"
    db = SessionLocal()
    try:
        recording = db.scalar(select(SessionRecording).where(SessionRecording.session_id == session_id))
        assert recording is not None
        recording.recording_url = None
        recording.realtimekit_recording_id = recording_id
        recording.storage_provider = "r2"
        recording.storage_key = f"live-sessions/{recording_id}.mp4"
        db.commit()
    finally:
        db.close()
    student = _make_user("recordings-test-r2")
    db = SessionLocal()
    try:
        db.add(CohortMember(cohort_id=cohort_id, user_id=student.id, role=CohortMemberRole.STUDENT))
        db.commit()
    finally:
        db.close()

    with (
        patch("app.services.cloudflare_stream.CloudflareStreamService.embed_url", return_value=None),
        patch(
            "app.services.cloudflare_stream.CloudflareStreamService.signed_playback_url",
            return_value=None,
        ),
        patch(
            "app.services.recording_archive.RecordingArchiveService.presigned_watch_url",
            return_value="https://r2.example/watch",
        ) as presign,
    ):
        resp = client.get(
            f"/api/v1/cohorts/{cohort_id}/sessions/{session_id}/recording",
            headers=_auth(student),
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["watch_url"] == "https://r2.example/watch"
    presign.assert_called()
    _cleanup()


def test_operations_can_read_report_and_attendance():
    _cleanup()
    cohort_id, _ = _seed()
    ops = _make_user("recordings-test-ops2", UserRole.OPERATIONS)

    report = client.get(f"/api/v1/instructor/cohorts/{cohort_id}/report", headers=_auth(ops))
    assert report.status_code == 200

    attendance = client.get(
        f"/api/v1/instructor/cohorts/{cohort_id}/attendance", headers=_auth(ops)
    )
    assert attendance.status_code == 200

    # A non-cohort staff role is still blocked.
    editor = _make_user("recordings-test-editor2", UserRole.EDITOR)
    assert (
        client.get(
            f"/api/v1/instructor/cohorts/{cohort_id}/report", headers=_auth(editor)
        ).status_code
        == 403
    )
    _cleanup()