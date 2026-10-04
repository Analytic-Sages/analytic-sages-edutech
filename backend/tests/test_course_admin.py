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
from app.models.course import Course
from app.models.user import User

client = TestClient(app)

SLUG_PREFIX = "course-authoring-test"


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
            email=f"course-authoring-{uuid.uuid4().hex[:8]}@example.com",
            full_name="Course Author",
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
        for course in db.scalars(
            select(Course).where(Course.slug.like(f"{SLUG_PREFIX}%"))
        ).all():
            db.delete(course)
        for user in db.scalars(
            select(User).where(User.email.like("course-authoring-%@example.com"))
        ).all():
            db.delete(user)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def author_env():
    _cleanup()
    yield
    _cleanup()


def test_course_authoring_requires_staff(author_env):
    student = _make_user(UserRole.STUDENT)
    try:
        assert (
            client.post("/api/v1/admin/courses", headers=_auth(student), json={}).status_code == 403
        )
    finally:
        _cleanup()


def test_full_course_authoring_flow(author_env):
    admin = _make_user(UserRole.ADMIN)
    slug = f"{SLUG_PREFIX}-{uuid.uuid4().hex[:6]}"
    try:
        created = client.post(
            "/api/v1/admin/courses",
            headers=_auth(admin),
            json={
                "slug": slug,
                "title": "Authoring Test Course",
                "description": "Created without a developer",
                "price": 0,
                "is_free": True,
                "published": False,
            },
        )
        assert created.status_code == 201, created.text
        assert created.json()["slug"] == slug
        assert created.json()["is_free"] is True

        # Duplicate slug rejected.
        dup = client.post(
            "/api/v1/admin/courses",
            headers=_auth(admin),
            json={"slug": slug, "title": "Dup"},
        )
        assert dup.status_code == 409

        # Add a module.
        module = client.post(
            f"/api/v1/admin/courses/{slug}/modules",
            headers=_auth(admin),
            json={"title": "Module 1", "description": "Foundations"},
        )
        assert module.status_code == 201
        module_id = module.json()["id"]
        assert module.json()["order_index"] == 1

        # Add lessons (order auto-assigned).
        lesson_one = client.post(
            f"/api/v1/admin/modules/{module_id}/lessons",
            headers=_auth(admin),
            json={"title": "Lesson One", "video_provider": "youtube", "video_id": "abc123"},
        )
        assert lesson_one.status_code == 201
        lesson_id = lesson_one.json()["id"]
        assert lesson_one.json()["slug"] == "lesson-one"
        assert lesson_one.json()["order_index"] == 1

        lesson_two = client.post(
            f"/api/v1/admin/modules/{module_id}/lessons",
            headers=_auth(admin),
            json={"title": "Lesson Two"},
        )
        assert lesson_two.status_code == 201
        assert lesson_two.json()["order_index"] == 2

        # Lesson slug must be unique within the course.
        dup_slug = client.post(
            f"/api/v1/admin/modules/{module_id}/lessons",
            headers=_auth(admin),
            json={"title": "Another", "slug": "lesson-one"},
        )
        assert dup_slug.status_code == 409

        # Attach a resource (by URL).
        resource = client.post(
            f"/api/v1/admin/lessons/{lesson_id}/resources",
            headers=_auth(admin),
            json={
                "label": "Starter notebook",
                "url": "/api/v1/media/abc.ipynb",
                "kind": "dataset",
            },
        )
        assert resource.status_code == 200
        assert resource.json()["resources"][0]["label"] == "Starter notebook"

        # Remove it.
        removed = client.request(
            "DELETE",
            f"/api/v1/admin/lessons/{lesson_id}/resources",
            headers=_auth(admin),
            params={"url": "/api/v1/media/abc.ipynb"},
        )
        assert removed.status_code == 200
        assert removed.json()["resources"] == []

        # lessons_count is synced on the course.
        detail = client.get(f"/api/v1/admin/courses/{slug}/detail", headers=_auth(admin))
        assert detail.status_code == 200
        body = detail.json()
        assert body["lessons_count"] == 2
        assert len(body["modules"]) == 1
        assert len(body["modules"][0]["lessons"]) == 2

        # Publish then confirm the public learner API sees it.
        published = client.patch(
            f"/api/v1/admin/courses/{slug}",
            headers=_auth(admin),
            json={"published": True},
        )
        assert published.status_code == 200
        assert published.json()["published"] is True

        public = client.get(f"/api/v1/self-paced/courses/{slug}")
        assert public.status_code == 200
        assert public.json()["title"] == "Authoring Test Course"
        assert len(public.json()["modules"]) == 1
    finally:
        _cleanup()


def test_delete_module_and_lesson_resync_counts(author_env):
    admin = _make_user(UserRole.ADMIN)
    slug = f"{SLUG_PREFIX}-{uuid.uuid4().hex[:6]}"
    try:
        client.post(
            "/api/v1/admin/courses",
            headers=_auth(admin),
            json={"slug": slug, "title": "Delete Flow", "price": 0, "is_free": True},
        )
        module = client.post(
            f"/api/v1/admin/courses/{slug}/modules",
            headers=_auth(admin),
            json={"title": "M1"},
        ).json()
        lesson = client.post(
            f"/api/v1/admin/modules/{module['id']}/lessons",
            headers=_auth(admin),
            json={"title": "L1"},
        ).json()

        client.delete(f"/api/v1/admin/lessons/{lesson['id']}", headers=_auth(admin))
        detail = client.get(f"/api/v1/admin/courses/{slug}/detail", headers=_auth(admin)).json()
        assert detail["lessons_count"] == 0

        assert (
            client.delete(f"/api/v1/admin/modules/{module['id']}", headers=_auth(admin)).status_code
            == 204
        )
        detail = client.get(f"/api/v1/admin/courses/{slug}/detail", headers=_auth(admin)).json()
        assert detail["modules"] == []
    finally:
        _cleanup()
        _cleanup()