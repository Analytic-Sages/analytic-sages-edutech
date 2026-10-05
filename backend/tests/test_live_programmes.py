from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.live import ProgrammeStatus
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
)
from app.models.programme import Programme
from app.models.user import User

client = TestClient(app)

PROG_SLUG = "test-live-programme"
COHORT_SLUG = "test-live-cohort"


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
            full_name="Live Test",
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
        programme = db.scalar(select(Programme).where(Programme.slug == PROG_SLUG))
        if programme:
            for cohort in list(
                db.scalars(select(Cohort).where(Cohort.programme_id == programme.id)).all()
            ):
                db.delete(cohort)
            db.delete(programme)
        # Fallback for any cohort created before programme_id linkage.
        for cohort in list(db.scalars(select(Cohort).where(Cohort.slug == COHORT_SLUG)).all()):
            db.delete(cohort)
        for row in list(db.scalars(select(User).where(User.email.like("%live-test-%@example.com"))).all()):
            db.delete(row)
        db.commit()
    finally:
        db.close()


def _seed() -> tuple[Programme, Cohort, LiveSession]:
    db = SessionLocal()
    try:
        programme = Programme(
            id=uuid.uuid4(),
            slug=PROG_SLUG,
            title="Test Live Programme",
            description="A test live programme",
            overview="Overview",
            status=ProgrammeStatus.ACTIVE,
        )
        db.add(programme)
        db.flush()
        cohort = Cohort(
            id=uuid.uuid4(),
            programme_id=programme.id,
            name="Test Live Cohort",
            slug=COHORT_SLUG,
            description="A test cohort",
            status=CohortStatus.OPEN,
            timezone="UTC",
            starts_at=datetime.now(UTC) - timedelta(days=7),
            ends_at=datetime.now(UTC) + timedelta(days=21),
        )
        db.add(cohort)
        db.flush()
        session = LiveSession(
            id=uuid.uuid4(),
            cohort_id=cohort.id,
            title="Session 1",
            week_label="Week 1",
            session_number=1,
            session_type=LiveSessionType.TEACHING,
            starts_at=datetime.now(UTC) + timedelta(days=1),
            ends_at=datetime.now(UTC) + timedelta(days=1, hours=2),
            status=LiveSessionStatus.SCHEDULED,
        )
        db.add(session)
        db.commit()
        return programme, cohort, session
    finally:
        db.close()


def test_programme_listing_and_my_enrollment():
    _cleanup()
    _seed()
    student = _make_user("live-test-student")
    instructor = _make_user("live-test-instructor", UserRole.INSTRUCTOR)
    db = SessionLocal()
    try:
        cohort = db.scalar(select(Cohort).where(Cohort.slug == COHORT_SLUG))
        db.add(CohortMember(cohort_id=cohort.id, user_id=student.id, role=CohortMemberRole.STUDENT))
        db.add(CohortMember(cohort_id=cohort.id, user_id=instructor.id, role=CohortMemberRole.INSTRUCTOR))
        db.commit()
    finally:
        db.close()

    public = client.get("/api/v1/programmes")
    assert public.status_code == 200
    assert any(p["slug"] == PROG_SLUG for p in public.json())

    detail = client.get(f"/api/v1/programmes/{PROG_SLUG}")
    assert detail.status_code == 200
    assert detail.json()["cohorts"][0]["slug"] == COHORT_SLUG

    mine = client.get("/api/v1/me/live", headers=_auth(student))
    assert mine.status_code == 200
    assert mine.json()[0]["cohort_slug"] == COHORT_SLUG

    stranger = _make_user("live-test-stranger")
    empty = client.get("/api/v1/me/live", headers=_auth(stranger))
    assert empty.json() == []

    _cleanup()

def test_student_cannot_access_another_cohort():
    _cleanup()
    _seed()
    student = _make_user("live-test-student")
    stranger = _make_user("live-test-stranger")
    db = SessionLocal()
    try:
        cohort = db.scalar(select(Cohort).where(Cohort.slug == COHORT_SLUG))
        db.add(CohortMember(cohort_id=cohort.id, user_id=student.id, role=CohortMemberRole.STUDENT))
        db.commit()
        cohort_id = str(cohort.id)
    finally:
        db.close()

    assert client.get(f"/api/v1/cohorts/{cohort_id}", headers=_auth(stranger)).status_code == 403
    assert client.get(f"/api/v1/cohorts/{cohort_id}", headers=_auth(student)).status_code == 200
    _cleanup()


def test_admin_previews_cohorts_as_student_view():
    _cleanup()
    _seed()
    admin = _make_user("live-test-admin", UserRole.ADMIN)
    db = SessionLocal()
    try:
        cohort = db.scalar(select(Cohort).where(Cohort.slug == COHORT_SLUG))
        cohort_id = str(cohort.id)
    finally:
        db.close()

    mine = client.get("/api/v1/me/live", headers=_auth(admin))
    assert mine.status_code == 200
    rows = mine.json()
    assert any(row["cohort_slug"] == COHORT_SLUG and row["is_preview"] is True for row in rows)
    assert rows[0]["enrollment_status"] == "preview"

    detail = client.get(f"/api/v1/cohorts/{cohort_id}", headers=_auth(admin))
    assert detail.status_code == 200
    body = detail.json()
    assert body["is_preview"] is True
    assert len(body["sessions"]) >= 1

    _cleanup()


def test_instructor_records_attendance_and_is_scoped():
    _cleanup()
    _seed()
    student = _make_user("live-test-student")
    other = _make_user("live-test-other")
    instructor = _make_user("live-test-instructor", UserRole.INSTRUCTOR)
    outsider = _make_user("live-test-outside-instructor", UserRole.INSTRUCTOR)
    db = SessionLocal()
    try:
        cohort = db.scalar(select(Cohort).where(Cohort.slug == COHORT_SLUG))
        session = db.scalar(select(LiveSession).where(LiveSession.cohort_id == cohort.id))
        db.add(CohortMember(cohort_id=cohort.id, user_id=student.id, role=CohortMemberRole.STUDENT))
        db.add(CohortMember(cohort_id=cohort.id, user_id=other.id, role=CohortMemberRole.STUDENT))
        db.add(CohortMember(cohort_id=cohort.id, user_id=instructor.id, role=CohortMemberRole.INSTRUCTOR))
        db.commit()
        cohort_id = str(cohort.id)
        session_id = str(session.id)
    finally:
        db.close()

    payload = {
        "items": [
            {"user_id": str(student.id), "session_id": session_id, "status": "attended"},
            {"user_id": str(other.id), "session_id": session_id, "status": "absent"},
        ]
    }
    recorded = client.put(
        f"/api/v1/instructor/cohorts/{cohort_id}/attendance",
        headers=_auth(instructor),
        json=payload,
    )
    assert recorded.status_code == 200

    mine = client.get(f"/api/v1/cohorts/{cohort_id}/attendance", headers=_auth(student))
    assert mine.status_code == 200
    assert len(mine.json()) == 1

    assert client.get(
        f"/api/v1/instructor/cohorts/{cohort_id}/students", headers=_auth(outsider)
    ).status_code == 403

    students = client.get(
        f"/api/v1/instructor/cohorts/{cohort_id}/students", headers=_auth(instructor)
    )
    assert students.status_code == 200
    assert len(students.json()) == 2
    _cleanup()

