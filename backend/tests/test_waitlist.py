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
from app.models.classroom import Cohort, CohortStatus
from app.models.user import User
from app.models.waitlist import CohortWaitlistEntry

client = TestClient(app)

COHORT_SLUG = "test-waitlist-cohort"


def _token_for(user: User) -> str:
    return SecurityService(get_settings()).create_access_token(
        user_id=str(user.id), role=user.role.value
    )


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_for(user)}"}


def _make_user(
    prefix: str,
    role: UserRole = UserRole.STUDENT,
    *,
    phone: str | None = None,
    discord: str | None = None,
    telegram: str | None = None,
) -> User:
    db = SessionLocal()
    try:
        user = User(
            email=f"{prefix}-{uuid.uuid4().hex[:8]}@example.com",
            full_name="Waitlist Test",
            role=role,
            email_verified=True,
            is_active=True,
            phone_number=phone,
            discord_username=discord,
            telegram_username=telegram,
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
            for entry in db.scalars(
                select(CohortWaitlistEntry).where(CohortWaitlistEntry.cohort_id == cohort.id)
            ).all():
                db.delete(entry)
            db.delete(cohort)
        for user in db.scalars(select(User).where(User.email.like("%waitlist-test-%@example.com"))).all():
            db.delete(user)
        db.commit()
    finally:
        db.close()


def _seed_cohort(*, started: bool = True, waitlist_flag: bool | None = None) -> Cohort:
    db = SessionLocal()
    try:
        if started:
            starts_at = datetime.now(UTC) - timedelta(days=7)
        else:
            starts_at = datetime.now(UTC) + timedelta(days=14)
        settings = {} if waitlist_flag is None else {"waitlist_open": waitlist_flag}
        cohort = Cohort(
            id=uuid.uuid4(),
            name="Waitlist Test Cohort",
            slug=COHORT_SLUG,
            description="",
            status=CohortStatus.OPEN,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(days=70),
            enrollment_settings=settings,
        )
        db.add(cohort)
        db.commit()
        db.refresh(cohort)
        return cohort
    finally:
        db.close()


def test_incomplete_profile_is_rejected_with_missing_fields():
    _cleanup()
    cohort = _seed_cohort()
    user = _make_user("waitlist-test-incomplete")

    resp = client.post(
        f"/api/v1/cohorts/{cohort.id}/waitlist",
        headers=_auth(user),
        json={"note": "Interested"},
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert set(detail["missing_fields"]) == {"phone_number", "discord_username", "telegram_username"}

    status = client.get(f"/api/v1/cohorts/{cohort.id}/waitlist/me", headers=_auth(user))
    assert status.status_code == 200
    body = status.json()
    assert body["is_on_waitlist"] is False
    assert body["is_open"] is True
    _cleanup()


def test_complete_profile_joins_and_is_idempotent():
    _cleanup()
    cohort = _seed_cohort()
    user = _make_user(
        "waitlist-test-complete",
        phone="8012345678",
        discord="tester#0001",
        telegram="@tester",
    )

    first = client.post(f"/api/v1/cohorts/{cohort.id}/waitlist", headers=_auth(user), json={})
    assert first.status_code == 200
    entry_id = first.json()["id"]

    # Joining again returns the same entry (no duplicate row).
    second = client.post(
        f"/api/v1/cohorts/{cohort.id}/waitlist",
        headers=_auth(user),
        json={"note": "Second visit"},
    )
    assert second.status_code == 200
    assert second.json()["id"] == entry_id

    status = client.get(f"/api/v1/cohorts/{cohort.id}/waitlist/me", headers=_auth(user))
    body = status.json()
    assert body["is_on_waitlist"] is True
    assert body["missing_fields"] == []

    db = SessionLocal()
    try:
        rows = list(
            db.scalars(
                select(CohortWaitlistEntry).where(CohortWaitlistEntry.cohort_id == cohort.id)
            ).all()
        )
        assert len(rows) == 1
    finally:
        db.close()
    _cleanup()


def test_admin_can_export_waitlist_entries():
    _cleanup()
    cohort = _seed_cohort()
    member = _make_user(
        "waitlist-test-member",
        phone="8099999999",
        discord="member#1234",
        telegram="@member",
    )
    admin = _make_user("waitlist-test-admin", UserRole.ADMIN)
    client.post(f"/api/v1/cohorts/{cohort.id}/waitlist", headers=_auth(member), json={})

    resp = client.get(f"/api/v1/admin/cohorts/{COHORT_SLUG}/waitlist", headers=_auth(admin))
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    row = body["entries"][0]
    assert row["email"] == member.email
    assert row["phone_number"] == "8099999999"
    assert row["discord_username"] == "member#1234"
    assert row["telegram_username"] == "@member"

    # Non-admins are rejected.
    forbidden = client.get(f"/api/v1/admin/cohorts/{COHORT_SLUG}/waitlist", headers=_auth(member))
    assert forbidden.status_code == 403
    _cleanup()


def test_waitlist_flag_and_auto_open_when_started():
    _cleanup()
    # Explicit flag off, not started → closed.
    _seed_cohort(started=False, waitlist_flag=False)
    public = client.get("/api/v1/classroom/public/cohorts")
    assert public.status_code == 200
    card = next(c for c in public.json() if c["slug"] == COHORT_SLUG)
    assert card["waitlist_open"] is False
    _cleanup()

    # No flag, but the cohort has started → auto-open.
    _seed_cohort(started=True, waitlist_flag=None)
    public = client.get("/api/v1/classroom/public/cohorts")
    card = next(c for c in public.json() if c["slug"] == COHORT_SLUG)
    assert card["waitlist_open"] is True
    _cleanup()