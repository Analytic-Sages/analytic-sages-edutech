"""Importing existing (historical) RealtimeKit recordings into LMS sessions.

All RealtimeKit + Cloudflare Stream responses are mocked — no live provider needed.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.attendance import Attendance
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
from app.services.cloudflare_stream import CloudflareStreamService, StreamVideo
from app.services.realtimekit import RealtimeKitService

client = TestClient(app)

COHORT_SLUG = "test-recording-import-cohort"
EMAIL_PREFIX = "recimport-"
RECORDING_ID = "fff4d97c-b29d-4a88-8fb6-0d46e13ee11c"
MEETING_A = "meeting-import-a"
MEETING_B = "meeting-import-b"
STREAM_UID = "stream-uid-import-1"


def _auth(user: User) -> dict[str, str]:
    token = SecurityService(get_settings()).create_access_token(
        user_id=str(user.id), role=user.role.value
    )
    return {"Authorization": f"Bearer {token}"}


def _make_user(prefix: str, role: UserRole = UserRole.STUDENT) -> User:
    db = SessionLocal()
    db.expire_on_commit = False
    try:
        user = User(
            email=f"{EMAIL_PREFIX}{prefix}-{uuid.uuid4().hex[:8]}@example.com",
            full_name=f"Import {prefix}",
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
        for user in db.scalars(select(User).where(User.email.like(f"{EMAIL_PREFIX}%"))).all():
            db.delete(user)
        db.commit()
    finally:
        db.close()


def _seed():
    """Cohort with two historical sessions (distinct meeting ids) + a student."""
    _cleanup()
    db = SessionLocal()
    db.expire_on_commit = False
    try:
        cohort = Cohort(
            id=uuid.uuid4(),
            name="Recording Import Cohort",
            slug=COHORT_SLUG,
            description="",
            status=CohortStatus.ACTIVE,
            starts_at=datetime(2026, 10, 5, tzinfo=UTC),
        )
        db.add(cohort)
        db.flush()

        session_a = LiveSession(
            id=uuid.uuid4(),
            cohort_id=cohort.id,
            title="Programme orientation & systems thinking",
            week_label="Week 0",
            session_number=1,
            session_type=LiveSessionType.TEACHING,
            starts_at=datetime(2026, 10, 5, 15, 0, tzinfo=UTC),
            ends_at=datetime(2026, 10, 5, 16, 30, tzinfo=UTC),
            status=LiveSessionStatus.ENDED,
            realtimekit_meeting_id=MEETING_A,
        )
        session_b = LiveSession(
            id=uuid.uuid4(),
            cohort_id=cohort.id,
            title="Second session",
            week_label="Week 1",
            session_number=2,
            session_type=LiveSessionType.TEACHING,
            starts_at=datetime(2026, 10, 7, 15, 0, tzinfo=UTC),
            ends_at=datetime(2026, 10, 7, 16, 30, tzinfo=UTC),
            status=LiveSessionStatus.ENDED,
            realtimekit_meeting_id=MEETING_B,
        )
        db.add_all([session_a, session_b])
        db.flush()

        student = User(
            email=f"{EMAIL_PREFIX}student-{uuid.uuid4().hex[:8]}@example.com",
            full_name="Import Student",
            role=UserRole.STUDENT,
            email_verified=True,
            is_active=True,
        )
        db.add(student)
        db.flush()
        db.add(
            CohortMember(cohort_id=cohort.id, user_id=student.id, role=CohortMemberRole.STUDENT)
        )
        db.commit()
        return cohort.id, session_a.id, session_b.id, student
    finally:
        db.close()


def _recording_detail(*, session_id="prov-session-1", url="https://rtk.example.com/tmp/rec.mp4"):
    return {
        "id": RECORDING_ID,
        "status": "UPLOADED",
        "download_url": url,
        "download_url_expiry": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
        "session_id": session_id,
        "started_time": datetime(2026, 10, 5, 15, 0, tzinfo=UTC).isoformat(),
        "recording_duration": 5400,
        "output_file_name": "Programme orientation & systems thinking",
    }


def _recording_listing(*, meeting_id=MEETING_A, title="Programme orientation & systems thinking"):
    return {
        "id": RECORDING_ID,
        "status": "UPLOADED",
        "download_url": "https://rtk.example.com/tmp/rec.mp4",
        "started_time": datetime(2026, 10, 5, 15, 0, tzinfo=UTC).isoformat(),
        "title": title,
        "meeting": {"id": meeting_id, "title": title},
    }


def _install_provider(monkeypatch, *, detail, listing):
    monkeypatch.setattr(RealtimeKitService, "get_recording", lambda self, rid: detail)
    monkeypatch.setattr(
        RealtimeKitService, "find_recording_in_list", lambda self, rid, max_pages=25: listing
    )
    monkeypatch.setattr(
        CloudflareStreamService,
        "copy_from_url",
        lambda self, *, url, meta=None, require_signed=None, max_duration_seconds=None: STREAM_UID,
    )
    monkeypatch.setattr(
        CloudflareStreamService,
        "get_video",
        lambda self, uid: StreamVideo(
            uid=uid, status="ready", duration_seconds=5400, thumbnail_url=None, embed_url=None, hls_url=None
        ),
    )
    monkeypatch.setattr(
        CloudflareStreamService,
        "embed_url",
        lambda self, uid: f"https://customer-test.cloudflarestream.com/{uid}/iframe",
    )
    monkeypatch.setattr(
        CloudflareStreamService,
        "signed_playback_url",
        lambda self, uid, ttl_seconds=3600: (
            f"https://customer-test.cloudflarestream.com/{uid}/iframe?token=signed"
        ),
    )


def _recording_row(session_id):
    db = SessionLocal()
    try:
        return db.scalar(
            select(SessionRecording).where(SessionRecording.session_id == session_id)
        )
    finally:
        db.close()


def test_preview_matches_session_by_meeting_id(monkeypatch):
    cohort_id, session_a, _session_b, _student = _seed()
    _install_provider(
        monkeypatch, detail=_recording_detail(), listing=_recording_listing(meeting_id=MEETING_A)
    )
    ops = _make_user("ops-preview", UserRole.OPERATIONS)

    resp = client.get(
        f"/api/v1/admin/classroom/recordings/import-preview?recording_id={RECORDING_ID}",
        headers=_auth(ops),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["meeting_id"] == MEETING_A
    assert body["title"] == "Programme orientation & systems thinking"
    assert body["already_linked_session_id"] is None
    assert body["ambiguous"] is False
    assert len(body["candidates"]) == 1
    assert body["candidates"][0]["session_id"] == str(session_a)
    assert body["candidates"][0]["match"] == "meeting"
    _cleanup()


def test_preview_resolves_meeting_via_provider_session_id(monkeypatch):
    """When the list item has no meeting object, resolve via session_id → associated_id."""
    _cohort_id, session_a, _session_b, _student = _seed()
    detail = _recording_detail(session_id="prov-session-x")
    _install_provider(monkeypatch, detail=detail, listing={"id": RECORDING_ID, "status": "UPLOADED"})
    monkeypatch.setattr(
        RealtimeKitService,
        "list_sessions",
        lambda self, associated_id=None, page_no=1, per_page=50: {
            "sessions": [{"id": "prov-session-x", "associated_id": MEETING_A}],
            "paging": {},
        },
    )
    ops = _make_user("ops-resolve", UserRole.OPERATIONS)

    resp = client.get(
        f"/api/v1/admin/classroom/recordings/import-preview?recording_id={RECORDING_ID}",
        headers=_auth(ops),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["meeting_id"] == MEETING_A
    assert body["provider_session_id"] == "prov-session-x"
    assert [c["session_id"] for c in body["candidates"]] == [str(session_a)]
    _cleanup()


def test_preview_without_metadata_has_no_candidates(monkeypatch):
    _seed()
    detail = {"id": RECORDING_ID, "status": "UPLOADED", "download_url": "https://rtk.example.com/x.mp4"}
    _install_provider(monkeypatch, detail=detail, listing={"id": RECORDING_ID, "status": "UPLOADED"})
    monkeypatch.setattr(
        RealtimeKitService,
        "list_sessions",
        lambda self, associated_id=None, page_no=1, per_page=50: {"sessions": [], "paging": {}},
    )
    ops = _make_user("ops-nomatch", UserRole.OPERATIONS)

    resp = client.get(
        f"/api/v1/admin/classroom/recordings/import-preview?recording_id={RECORDING_ID}",
        headers=_auth(ops),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["meeting_id"] is None
    assert body["candidates"] == []
    assert body["ambiguous"] is False
    assert body["note"] and "download url and a reason" in body["note"].lower()
    _cleanup()


def test_preview_is_ambiguous_when_multiple_sessions_share_meeting(monkeypatch):
    _cohort_id, session_a, session_b, _student = _seed()
    # Point both sessions at the same meeting id so two candidates match.
    db = SessionLocal()
    try:
        test_client_session = db.get(LiveSession, session_b)
        test_client_session.realtimekit_meeting_id = MEETING_A
        db.commit()
    finally:
        db.close()

    _install_provider(
        monkeypatch, detail=_recording_detail(), listing=_recording_listing(meeting_id=MEETING_A)
    )
    ops = _make_user("ops-ambiguous", UserRole.OPERATIONS)

    resp = client.get(
        f"/api/v1/admin/classroom/recordings/import-preview?recording_id={RECORDING_ID}",
        headers=_auth(ops),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ambiguous"] is True
    assert len(body["candidates"]) == 2
    assert {c["session_id"] for c in body["candidates"]} == {str(session_a), str(session_b)}
    _cleanup()


def test_preview_matches_exact_title_and_date(monkeypatch):
    _cohort_id, session_a, _session_b, _student = _seed()
    detail = _recording_detail()
    detail.pop("session_id", None)
    listing = {
        "id": RECORDING_ID,
        "status": "UPLOADED",
        "download_url": "https://rtk.example.com/tmp/rec.mp4",
        "started_time": datetime(2026, 10, 5, 15, 0, tzinfo=UTC).isoformat(),
        "title": "Programme orientation & systems thinking",
    }
    _install_provider(monkeypatch, detail=detail, listing=listing)
    monkeypatch.setattr(
        RealtimeKitService,
        "list_sessions",
        lambda self, associated_id=None, page_no=1, per_page=50: {"sessions": [], "paging": {}},
    )
    ops = _make_user("ops-title", UserRole.OPERATIONS)

    resp = client.get(
        f"/api/v1/admin/classroom/recordings/import-preview?recording_id={RECORDING_ID}",
        headers=_auth(ops),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["meeting_id"] is None
    assert body["ambiguous"] is False
    assert [c["session_id"] for c in body["candidates"]] == [str(session_a)]
    assert body["candidates"][0]["match"] == "title"
    _cleanup()


def test_preview_date_only_is_not_a_candidate(monkeypatch):
    _seed()
    detail = {
        "id": RECORDING_ID,
        "status": "UPLOADED",
        "download_url": "https://rtk.example.com/tmp/rec.mp4",
        "started_time": datetime(2026, 10, 5, 15, 0, tzinfo=UTC).isoformat(),
    }
    _install_provider(monkeypatch, detail=detail, listing={"id": RECORDING_ID, "status": "UPLOADED"})
    monkeypatch.setattr(
        RealtimeKitService,
        "list_sessions",
        lambda self, associated_id=None, page_no=1, per_page=50: {"sessions": [], "paging": {}},
    )
    ops = _make_user("ops-date", UserRole.OPERATIONS)

    resp = client.get(
        f"/api/v1/admin/classroom/recordings/import-preview?recording_id={RECORDING_ID}",
        headers=_auth(ops),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["candidates"] == []
    assert body["ambiguous"] is False
    _cleanup()


def test_preview_title_on_a_different_day_is_not_a_candidate(monkeypatch):
    _seed()
    detail = {
        "id": RECORDING_ID,
        "status": "UPLOADED",
        "started_time": datetime(2026, 10, 8, 15, 0, tzinfo=UTC).isoformat(),
        "output_file_name": "Programme orientation & systems thinking",
    }
    _install_provider(
        monkeypatch,
        detail=detail,
        listing={"id": RECORDING_ID, "status": "UPLOADED", "title": detail["output_file_name"]},
    )
    monkeypatch.setattr(
        RealtimeKitService,
        "list_sessions",
        lambda self, associated_id=None, page_no=1, per_page=50: {"sessions": [], "paging": {}},
    )
    ops = _make_user("ops-day", UserRole.OPERATIONS)

    resp = client.get(
        f"/api/v1/admin/classroom/recordings/import-preview?recording_id={RECORDING_ID}",
        headers=_auth(ops),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["candidates"] == []
    _cleanup()


def test_import_links_recording_and_is_idempotent(monkeypatch):
    cohort_id, session_a, _session_b, _student = _seed()
    _install_provider(
        monkeypatch, detail=_recording_detail(), listing=_recording_listing(meeting_id=MEETING_A)
    )
    admin = _make_user("admin-import", UserRole.ADMIN)
    url = f"/api/v1/admin/classroom/sessions/{session_a}/import-recording"
    payload = {"recording_id": RECORDING_ID}

    first = client.post(url, headers=_auth(admin), json=payload)
    assert first.status_code == 200, first.text
    assert first.json()["recording_status"] == "ready"

    row = _recording_row(session_a)
    assert row is not None
    assert row.provider_recording_id == STREAM_UID
    assert row.realtimekit_recording_id == RECORDING_ID
    assert row.status == RecordingStatus.READY
    # The expiring RealtimeKit URL is never stored as the recording.
    assert "rtk.example.com" not in (row.recording_url or "")

    # Repeated import is idempotent — still exactly one row, same Stream uid.
    second = client.post(url, headers=_auth(admin), json=payload)
    assert second.status_code == 200, second.text
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(SessionRecording).where(SessionRecording.session_id == session_a)
        ).all()
    finally:
        db.close()
    assert len(rows) == 1
    assert rows[0].provider_recording_id == STREAM_UID
    _cleanup()


def test_import_refuses_duplicate_across_sessions(monkeypatch):
    _cohort_id, session_a, session_b, _student = _seed()
    _install_provider(
        monkeypatch, detail=_recording_detail(), listing=_recording_listing(meeting_id=MEETING_A)
    )
    admin = _make_user("admin-dup", UserRole.ADMIN)

    first = client.post(
        f"/api/v1/admin/classroom/sessions/{session_a}/import-recording",
        headers=_auth(admin),
        json={"recording_id": RECORDING_ID},
    )
    assert first.status_code == 200, first.text

    # The same RealtimeKit recording must not be linked to a second session.
    dup = client.post(
        f"/api/v1/admin/classroom/sessions/{session_b}/import-recording",
        headers=_auth(admin),
        json={"recording_id": RECORDING_ID},
    )
    assert dup.status_code == 409
    assert _recording_row(session_b) is None
    _cleanup()


def test_import_rejects_a_session_the_metadata_does_not_match(monkeypatch):
    _cohort_id, _session_a, session_b, _student = _seed()
    _install_provider(
        monkeypatch, detail=_recording_detail(), listing=_recording_listing(meeting_id=MEETING_A)
    )
    admin = _make_user("admin-wrong", UserRole.ADMIN)

    resp = client.post(
        f"/api/v1/admin/classroom/sessions/{session_b}/import-recording",
        headers=_auth(admin),
        json={"recording_id": RECORDING_ID},
    )
    assert resp.status_code == 400
    assert _recording_row(session_b) is None
    _cleanup()


def test_import_rejects_ambiguous_match_without_manual_recovery(monkeypatch):
    _cohort_id, session_a, session_b, _student = _seed()
    db = SessionLocal()
    try:
        row = db.get(LiveSession, session_b)
        row.realtimekit_meeting_id = MEETING_A
        db.commit()
    finally:
        db.close()
    _install_provider(
        monkeypatch, detail=_recording_detail(), listing=_recording_listing(meeting_id=MEETING_A)
    )
    admin = _make_user("admin-ambig", UserRole.ADMIN)

    blocked = client.post(
        f"/api/v1/admin/classroom/sessions/{session_a}/import-recording",
        headers=_auth(admin),
        json={"recording_id": RECORDING_ID},
    )
    assert blocked.status_code == 400
    assert _recording_row(session_a) is None

    allowed = client.post(
        f"/api/v1/admin/classroom/sessions/{session_a}/import-recording",
        headers=_auth(admin),
        json={
            "recording_id": RECORDING_ID,
            "download_url": "https://rtk.example.com/manual/rec.mp4",
            "reason": "Both sessions share the meeting id; this is the orientation session.",
        },
    )
    assert allowed.status_code == 200, allowed.text
    assert _recording_row(session_a) is not None
    assert _recording_row(session_b) is None
    _cleanup()


def test_import_manual_download_url_fallback(monkeypatch):
    """Recovery path: the recording API can't return it, but a URL is supplied."""
    _cohort_id, session_a, _session_b, _student = _seed()
    _install_provider(monkeypatch, detail=None, listing=None)
    admin = _make_user("admin-manual", UserRole.ADMIN)

    resp = client.post(
        f"/api/v1/admin/classroom/sessions/{session_a}/import-recording",
        headers=_auth(admin),
        json={
            "recording_id": RECORDING_ID,
            "download_url": "https://rtk.example.com/manual/rec.mp4",
            "reason": "Recovered from the RealtimeKit dashboard download link",
        },
    )
    assert resp.status_code == 200, resp.text
    row = _recording_row(session_a)
    assert row.provider_recording_id == STREAM_UID
    assert row.realtimekit_recording_id == RECORDING_ID
    assert row.status == RecordingStatus.READY
    _cleanup()


def test_import_without_download_url_returns_400(monkeypatch):
    _cohort_id, session_a, _session_b, _student = _seed()
    _install_provider(monkeypatch, detail=None, listing=None)
    admin = _make_user("admin-nourl", UserRole.ADMIN)

    resp = client.post(
        f"/api/v1/admin/classroom/sessions/{session_a}/import-recording",
        headers=_auth(admin),
        json={"recording_id": RECORDING_ID},
    )
    assert resp.status_code == 400
    assert _recording_row(session_a) is None
    _cleanup()
def test_enrolled_student_can_watch_imported_recording_and_stranger_cannot(monkeypatch):
    cohort_id, session_a, _session_b, student = _seed()
    _install_provider(
        monkeypatch, detail=_recording_detail(), listing=_recording_listing(meeting_id=MEETING_A)
    )
    admin = _make_user("admin-watch", UserRole.ADMIN)
    client.post(
        f"/api/v1/admin/classroom/sessions/{session_a}/import-recording",
        headers=_auth(admin),
        json={"recording_id": RECORDING_ID},
    )
    db = SessionLocal()
    try:
        stored = db.get(LiveSession, session_a)
        stored.recording_url = "https://rtk.example.com/tmp/rec.mp4"
        db.commit()
    finally:
        db.close()

    enrolled = client.get(
        f"/api/v1/cohorts/{cohort_id}/sessions/{session_a}/recording", headers=_auth(student)
    )
    assert enrolled.status_code == 200, enrolled.text
    assert enrolled.json()["status"] == "ready"
    assert enrolled.json()["watch_url"]
    assert "rtk.example.com" not in enrolled.json()["watch_url"]
    assert "cloudflarestream.com" in enrolled.json()["watch_url"]

    stranger = _make_user("stranger")
    denied = client.get(
        f"/api/v1/cohorts/{cohort_id}/sessions/{session_a}/recording", headers=_auth(stranger)
    )
    assert denied.status_code == 403

    # The recording is only linked to the correct session — not the other one.
    assert _recording_row(session_a) is not None
    db = SessionLocal()
    try:
        other = db.scalar(
            select(SessionRecording).where(SessionRecording.session_id == _session_b)
        )
    finally:
        db.close()
    assert other is None
    _cleanup()


def test_unauthorized_cannot_preview_or_import(monkeypatch):
    _cohort_id, session_a, _session_b, _student = _seed()
    _install_provider(
        monkeypatch, detail=_recording_detail(), listing=_recording_listing(meeting_id=MEETING_A)
    )
    editor = _make_user("editor-no", UserRole.EDITOR)
    student = _make_user("student-no", UserRole.STUDENT)

    for user in (editor, student):
        preview = client.get(
            f"/api/v1/admin/classroom/recordings/import-preview?recording_id={RECORDING_ID}",
            headers=_auth(user),
        )
        assert preview.status_code == 403
        imported = client.post(
            f"/api/v1/admin/classroom/sessions/{session_a}/import-recording",
            headers=_auth(user),
            json={"recording_id": RECORDING_ID},
        )
        assert imported.status_code == 403
    _cleanup()


def test_import_does_not_touch_attendance(monkeypatch):
    _cohort_id, session_a, _session_b, student = _seed()
    db = SessionLocal()
    try:
        db.add(
            Attendance(
                id=uuid.uuid4(),
                session_id=session_a,
                user_id=student.id,
                status="attended",
            )
        )
        db.commit()
    finally:
        db.close()

    _install_provider(
        monkeypatch, detail=_recording_detail(), listing=_recording_listing(meeting_id=MEETING_A)
    )
    admin = _make_user("admin-attendance", UserRole.ADMIN)
    resp = client.post(
        f"/api/v1/admin/classroom/sessions/{session_a}/import-recording",
        headers=_auth(admin),
        json={"recording_id": RECORDING_ID},
    )
    assert resp.status_code == 200, resp.text

    db = SessionLocal()
    try:
        rows = db.scalars(
            select(Attendance).where(Attendance.session_id == session_a)
        ).all()
    finally:
        db.close()
    assert len(rows) == 1
    assert rows[0].status.value == "attended"
    _cleanup()