from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.event import Event, EventRegistration, EventType
from app.models.user import User
from app.services.email import EmailService

client = TestClient(app)

SLUG = "test-dune-workshop"


def _token_for(user: User) -> str:
    return SecurityService(get_settings()).create_access_token(
        user_id=str(user.id), role=user.role.value
    )


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_for(user)}"}


def _make_user(email: str, role: UserRole = UserRole.STUDENT) -> User:
    db = SessionLocal()
    try:
        user = User(
            email=email,
            full_name="Test Student",
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


def _cleanup_slug(slug: str) -> None:
    db = SessionLocal()
    try:
        event = db.scalar(select(Event).where(Event.slug == slug))
        if event:
            db.delete(event)
            db.commit()
    finally:
        db.close()


def _seed_event(
    *,
    slug: str = SLUG,
    published: bool = True,
    cancelled: bool = False,
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
    youtube_live_url: str | None = "https://www.youtube.com/watch?v=example",
    recording_url: str | None = None,
    capacity: int | None = None,
    price: int = 0,
) -> Event:
    _cleanup_slug(slug)
    now = datetime.now(UTC)
    db = SessionLocal()
    try:
        event = Event(
            slug=slug,
            title="Test Dune Workshop",
            event_type=EventType.WORKSHOP,
            short_description="A test workshop.",
            description="Longer description for the test workshop.",
            cover_image="/4.png",
            starts_at=starts_at or (now + timedelta(days=7)),
            ends_at=ends_at or (now + timedelta(days=7, hours=2)),
            timezone="Africa/Lagos",
            price=price,
            currency="USD",
            capacity=capacity,
            host_name="Analytic Sages",
            youtube_live_url=youtube_live_url,
            recording_url=recording_url,
            learn_topics=["Dune SQL"],
            audience=["Analysts"],
            prerequisites="",
            published=published,
            cancelled=cancelled,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    finally:
        db.close()


def test_unpublished_events_are_hidden():
    _seed_event(published=False)
    listed = client.get("/api/v1/events")
    assert listed.status_code == 200
    assert all(row["slug"] != SLUG for row in listed.json())
    assert client.get(f"/api/v1/events/{SLUG}").status_code == 404


def test_public_event_lists_without_auth():
    _seed_event()
    listed = client.get("/api/v1/events")
    assert listed.status_code == 200
    assert any(row["slug"] == SLUG for row in listed.json())
    detail = client.get(f"/api/v1/events/{SLUG}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["registered"] is False
    assert body["is_free"] is True
    assert body["youtube_live_url"] is None
    assert body["can_register"] is True


def test_register_requires_auth_and_is_idempotent(monkeypatch):
    monkeypatch.setattr(EmailService, "send_event_registration_email", lambda *args, **kwargs: None)
    _seed_event()
    assert client.post(f"/api/v1/events/{SLUG}/register").status_code == 401

    user = _make_user(f"rsvp-{uuid.uuid4()}@example.com")
    first = client.post(f"/api/v1/events/{SLUG}/register", headers=_auth(user), json={})
    second = client.post(f"/api/v1/events/{SLUG}/register", headers=_auth(user), json={})
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["registration_id"] == second.json()["registration_id"]
    assert second.json()["already_registered"] is True

    db = SessionLocal()
    try:
        count = db.scalar(
            select(func.count())
            .select_from(EventRegistration)
            .where(EventRegistration.user_id == user.id)
        )
        assert count == 1
    finally:
        db.close()

    mine = client.get("/api/v1/events/me", headers=_auth(user))
    assert mine.status_code == 200
    assert any(row["event"]["slug"] == SLUG for row in mine.json())

    detail = client.get(f"/api/v1/events/{SLUG}", headers=_auth(user))
    assert detail.json()["registered"] is True
    assert detail.json()["youtube_live_url"] is not None


def test_join_records_click_and_requires_registration(monkeypatch):
    monkeypatch.setattr(EmailService, "send_event_registration_email", lambda *args, **kwargs: None)
    now = datetime.now(UTC)
    _seed_event(starts_at=now - timedelta(minutes=5), ends_at=now + timedelta(hours=1))
    outsider = _make_user(f"out-{uuid.uuid4()}@example.com")
    assert (
        client.post(f"/api/v1/events/{SLUG}/join", headers=_auth(outsider)).status_code == 403
    )

    user = _make_user(f"join-{uuid.uuid4()}@example.com")
    client.post(f"/api/v1/events/{SLUG}/register", headers=_auth(user), json={})
    joined = client.post(f"/api/v1/events/{SLUG}/join", headers=_auth(user))
    assert joined.status_code == 200
    assert "youtube.com" in joined.json()["youtube_live_url"]

    db = SessionLocal()
    try:
        row = db.scalar(select(EventRegistration).where(EventRegistration.user_id == user.id))
        assert row is not None
        assert row.join_clicked_at is not None
        assert row.checked_in_at is not None
    finally:
        db.close()


def test_admin_crud_requires_admin(monkeypatch):
    monkeypatch.setattr(EmailService, "send_event_registration_email", lambda *args, **kwargs: None)
    student = _make_user(f"student-{uuid.uuid4()}@example.com")
    assert client.get("/api/v1/admin/events", headers=_auth(student)).status_code == 403
    assert client.get("/api/v1/admin/events").status_code == 401

    admin = _make_user(f"admin-{uuid.uuid4()}@example.com", role=UserRole.ADMIN)
    created = client.post(
        "/api/v1/admin/events",
        headers=_auth(admin),
        json={
            "slug": f"admin-event-{uuid.uuid4().hex[:8]}",
            "title": "Admin Created Workshop",
            "event_type": "workshop",
            "short_description": "Created from tests.",
            "description": "Created from tests.",
            "starts_at": (datetime.now(UTC) + timedelta(days=14)).isoformat(),
            "ends_at": (datetime.now(UTC) + timedelta(days=14, hours=2)).isoformat(),
            "timezone": "Africa/Lagos",
            "published": True,
            "learn_topics": ["SQL"],
            "audience": ["Builders"],
        },
    )
    assert created.status_code == 201
    event_id = created.json()["id"]
    listed = client.get("/api/v1/admin/events", headers=_auth(admin))
    assert any(row["id"] == event_id for row in listed.json())

    cancelled = client.post(f"/api/v1/admin/events/{event_id}/cancel", headers=_auth(admin))
    assert cancelled.status_code == 200
    assert cancelled.json()["cancelled"] is True
    assert cancelled.json()["lifecycle"] == "cancelled"


def test_coming_soon_event_is_visible_but_not_registerable():
    _cleanup_slug(SLUG)
    db = SessionLocal()
    try:
        event = Event(
            slug=SLUG,
            title="Coming Soon Workshop",
            event_type=EventType.WORKSHOP,
            short_description="Date to be announced.",
            description="Date to be announced.",
            starts_at=None,
            ends_at=None,
            timezone="Africa/Lagos",
            price=0,
            currency="USD",
            learn_topics=[],
            audience=[],
            published=True,
            cancelled=False,
        )
        db.add(event)
        db.commit()
    finally:
        db.close()

    listed = client.get("/api/v1/events?upcoming=true")
    assert listed.status_code == 200
    row = next(item for item in listed.json() if item["slug"] == SLUG)
    assert row["lifecycle"] == "coming_soon"
    assert row["can_register"] is False
    assert row["starts_at"] is None

    user = _make_user(f"soon-{uuid.uuid4()}@example.com")
    blocked = client.post(f"/api/v1/events/{SLUG}/register", headers=_auth(user), json={})
    assert blocked.status_code == 400
    _cleanup_slug(SLUG)


def test_operations_can_manage_events_but_not_users():
    ops = _make_user(f"ops-{uuid.uuid4()}@example.com", role=UserRole.OPERATIONS)
    created = client.post(
        "/api/v1/admin/events",
        headers=_auth(ops),
        json={
            "slug": f"ops-event-{uuid.uuid4().hex[:8]}",
            "title": "Ops Coming Soon",
            "event_type": "workshop",
            "short_description": "Created by operations.",
            "description": "Created by operations.",
            "timezone": "Africa/Lagos",
            "published": True,
        },
    )
    assert created.status_code == 201
    assert created.json()["lifecycle"] == "coming_soon"
    assert created.json()["starts_at"] is None

    event_id = created.json()["id"]
    patched = client.patch(
        f"/api/v1/admin/events/{event_id}",
        headers=_auth(ops),
        json={"title": "Ops Updated Event"},
    )
    assert patched.status_code == 200
    assert patched.json()["title"] == "Ops Updated Event"

    assert client.get("/api/v1/admin/users", headers=_auth(ops)).status_code == 403
    assert client.get("/api/v1/admin/overview", headers=_auth(ops)).status_code == 403
    _cleanup_slug(created.json()["slug"])
