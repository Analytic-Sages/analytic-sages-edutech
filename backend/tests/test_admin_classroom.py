from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.classroom import Cohort, CohortMember, CohortMemberRole
from app.models.user import User
from app.services.classroom import ClassroomService
from app.services.seed_bde_classroom import seed_bde_classroom

client = TestClient(app)

BDE_COHORT_SLUG = "blockchain-data-engineering"


def _token_for(user: User) -> str:
    return SecurityService(get_settings()).create_access_token(
        user_id=str(user.id), role=user.role.value
    )


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_for(user)}"}


def _make_user(role: UserRole) -> User:
    db = SessionLocal()
    try:
        user = User(
            email=f"admin-classroom-{uuid.uuid4()}@example.com",
            full_name="Admin Classroom",
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


def _cleanup_user(user: User) -> None:
    db = SessionLocal()
    try:
        row = db.get(User, user.id)
        if row:
            db.delete(row)
            db.commit()
    finally:
        db.close()


def _featured_cohort_id():
    db = SessionLocal()
    try:
        seed_bde_classroom(db)
        cohort = db.scalar(select(Cohort).where(Cohort.slug == BDE_COHORT_SLUG))
        return cohort.id
    finally:
        db.close()


def test_admin_classroom_requires_admin():
    student = _make_user(UserRole.STUDENT)
    try:
        assert client.get("/api/v1/admin/classroom/sessions", headers=_auth(student)).status_code == 403
        assert client.get("/api/v1/admin/classroom/cohorts", headers=_auth(student)).status_code == 403
    finally:
        _cleanup_user(student)


def test_cohort_options_list_includes_featured_cohort():
    admin = _make_user(UserRole.ADMIN)
    try:
        _featured_cohort_id()
        response = client.get("/api/v1/admin/classroom/cohorts", headers=_auth(admin))
        assert response.status_code == 200
        slugs = {row["slug"] for row in response.json()}
        assert BDE_COHORT_SLUG in slugs
    finally:
        _cleanup_user(admin)


def test_internal_sync_schedule_is_token_protected_and_idempotent(monkeypatch):
    """Ops hook that guarantees the complete 40-session BDE schedule in any env."""
    settings = get_settings()
    monkeypatch.setattr(settings, "classroom_sync_token", "classroom-token")
    monkeypatch.setattr(settings, "opportunity_sync_token", None)

    url = "/api/v1/internal/classroom/sync-schedule"

    # Missing token → unauthorized (the token is set, so this is not a 404).
    assert client.post(url).status_code == 401
    # Wrong token → unauthorized.
    assert (
        client.post(url, headers={"X-Classroom-Sync-Token": "nope"}).status_code == 401
    )
    # Correct token → full canonical schedule, idempotent.
    response = client.post(url, headers={"X-Classroom-Sync-Token": "classroom-token"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 40
    assert body["created"] + body["updated"] == 40


def test_internal_sync_schedule_disabled_when_no_token(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "classroom_sync_token", None)
    monkeypatch.setattr(settings, "opportunity_sync_token", None)
    response = client.post(
        "/api/v1/internal/classroom/sync-schedule",
        headers={"X-Classroom-Sync-Token": "anything"},
    )
    assert response.status_code == 404


def test_admin_can_create_edit_cancel_and_delete_session():
    admin = _make_user(UserRole.ADMIN)
    student = _make_user(UserRole.STUDENT)
    try:
        cohort_id = str(_featured_cohort_id())
        db = SessionLocal()
        try:
            db.add(
                CohortMember(cohort_id=cohort_id, user_id=student.id, role=CohortMemberRole.STUDENT)
            )
            db.commit()
        finally:
            db.close()

        starts = datetime.now(timezone.utc) + timedelta(days=30)
        payload = {
            "cohort_id": cohort_id,
            "title": "One-off Guest Workshop",
            "week_label": "Bonus",
            "session_number": 99,
            "session_type": "teaching",
            "objectives": ["Cover a guest topic"],
            "starts_at": starts.isoformat(),
            "ends_at": (starts + timedelta(hours=2)).isoformat(),
        }
        created = client.post(
            "/api/v1/admin/classroom/sessions", headers=_auth(admin), json=payload
        )
        assert created.status_code == 201, created.text
        session_id = created.json()["id"]
        assert created.json()["title"] == "One-off Guest Workshop"
        assert created.json()["phase"] == "upcoming"

        # Duplicate slot is rejected.
        dup = client.post("/api/v1/admin/classroom/sessions", headers=_auth(admin), json=payload)
        assert dup.status_code == 409

        # Visible to a student in the cohort.
        db = SessionLocal()
        try:
            sessions = ClassroomService(db, get_settings()).list_my_sessions(student)
            assert any(str(s.id) == session_id for s in sessions)
        finally:
            db.close()

        # Edit.
        patched = client.patch(
            f"/api/v1/admin/classroom/sessions/{session_id}",
            headers=_auth(admin),
            json={"title": "Guest Workshop (Updated)"},
        )
        assert patched.status_code == 200
        assert patched.json()["title"] == "Guest Workshop (Updated)"

        # Cancel.
        cancelled = client.post(
            f"/api/v1/admin/classroom/sessions/{session_id}/cancel", headers=_auth(admin)
        )
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "cancelled"
        assert cancelled.json()["phase"] == "cancelled"

        # Delete.
        deleted = client.delete(
            f"/api/v1/admin/classroom/sessions/{session_id}", headers=_auth(admin)
        )
        assert deleted.status_code == 204
    finally:
        _cleanup_user(admin)
        _cleanup_user(student)


def test_create_rejects_end_before_start():
    admin = _make_user(UserRole.ADMIN)
    try:
        cohort_id = str(_featured_cohort_id())
        starts = datetime.now(timezone.utc) + timedelta(days=45)
        payload = {
            "cohort_id": cohort_id,
            "title": "Bad window",
            "session_number": 98,
            "session_type": "office_hour",
            "starts_at": starts.isoformat(),
            "ends_at": (starts - timedelta(hours=1)).isoformat(),
        }
        response = client.post(
            "/api/v1/admin/classroom/sessions", headers=_auth(admin), json=payload
        )
        assert response.status_code == 400
    finally:
        _cleanup_user(admin)