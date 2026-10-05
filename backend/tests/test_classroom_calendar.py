from __future__ import annotations

import uuid

import pytest
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


@pytest.fixture(scope="module", autouse=True)
def _ensure_bde_seeded():
    """Guarantee the BDE cohort + schedule exist regardless of scripts run."""
    db = SessionLocal()
    try:
        seed_bde_classroom(db)
    finally:
        db.close()


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
            email=f"calendar-{uuid.uuid4()}@example.com",
            full_name="Calendar Tester",
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


def _join_bde(user: User) -> None:
    db = SessionLocal()
    try:
        cohort = db.scalar(select(Cohort).where(Cohort.slug == BDE_COHORT_SLUG))
        assert cohort is not None, "Run scripts/seed_blockchain_data_engineering.py first"
        db.add(
            CohortMember(
                cohort_id=cohort.id,
                user_id=user.id,
                role=CohortMemberRole.STUDENT,
            )
        )
        db.commit()
    finally:
        db.close()


def _expected_count(user: User) -> int:
    db = SessionLocal()
    try:
        return len(ClassroomService(db, get_settings()).list_my_sessions(user))
    finally:
        db.close()


def test_calendar_feed_requires_auth():
    assert client.get("/api/v1/classroom/calendar.ics").status_code == 401


def test_calendar_feed_rejects_bad_token():
    response = client.get("/api/v1/classroom/calendar.ics?token=not-a-real-token")
    assert response.status_code == 401


def test_enrolled_student_feed_has_events_and_reminders():
    student = _make_user(UserRole.STUDENT)
    try:
        _join_bde(student)
        expected = _expected_count(student)
        assert expected >= 30

        response = client.get("/api/v1/classroom/calendar.ics", headers=_auth(student))
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/calendar")

        body = response.text
        assert body.startswith("BEGIN:VCALENDAR")
        assert body.rstrip().endswith("END:VCALENDAR")
        assert body.count("BEGIN:VEVENT") == expected
        assert body.count("BEGIN:VALARM") == expected
        assert "TRIGGER:-PT15M" in body
    finally:
        _cleanup_user(student)


def test_student_without_membership_gets_empty_calendar():
    outsider = _make_user(UserRole.STUDENT)
    try:
        response = client.get("/api/v1/classroom/calendar.ics", headers=_auth(outsider))
        assert response.status_code == 200
        assert response.text.count("BEGIN:VEVENT") == 0
    finally:
        _cleanup_user(outsider)


def test_staff_feed_sees_at_least_as_much_as_a_student():
    student = _make_user(UserRole.STUDENT)
    admin = _make_user(UserRole.ADMIN)
    try:
        _join_bde(student)
        student_events = client.get(
            "/api/v1/classroom/calendar.ics", headers=_auth(student)
        ).text.count("BEGIN:VEVENT")
        staff_events = client.get(
            "/api/v1/classroom/calendar.ics", headers=_auth(admin)
        ).text.count("BEGIN:VEVENT")
        assert staff_events >= student_events >= 30
    finally:
        _cleanup_user(student)
        _cleanup_user(admin)


def test_calendar_token_roundtrip_via_query_param():
    student = _make_user(UserRole.STUDENT)
    try:
        _join_bde(student)
        token_response = client.get("/api/v1/classroom/calendar-token", headers=_auth(student))
        assert token_response.status_code == 200
        payload = token_response.json()
        assert payload["url"].startswith("http")
        assert "token=" in payload["url"]
        assert payload["webcal_url"].startswith("webcal://")

        feed = client.get(f"/api/v1/classroom/calendar.ics?token={payload['token']}")
        assert feed.status_code == 200
        assert feed.headers["content-type"].startswith("text/calendar")
        assert feed.text.count("BEGIN:VEVENT") == _expected_count(student)
    finally:
        _cleanup_user(student)