from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lms import CourseModule, Lesson, LessonProgress
from app.models.user import User

client = TestClient(app)

COURSE_SLUG = "test-self-paced-sql"
LESSON_ONE = "lesson-one"
LESSON_TWO = "lesson-two"


def _token_for(user: User) -> str:
    return SecurityService(get_settings()).create_access_token(
        user_id=str(user.id), role=user.role.value
    )


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_for(user)}"}


def _make_user(email: str) -> User:
    db = SessionLocal()
    try:
        user = User(
            email=email,
            full_name="Test Student",
            role=UserRole.STUDENT,
            email_verified=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def _seed_course() -> None:
    db = SessionLocal()
    try:
        existing = db.scalar(select(Course).where(Course.slug == COURSE_SLUG))
        if existing:
            return
        course = Course(
            id=uuid.uuid4(),
            slug=COURSE_SLUG,
            title="Test Self-Paced Course",
            description="A tiny curriculum for API tests.",
            long_description="A tiny curriculum for API tests.",
            category="Blockchain",
            difficulty="Beginner",
            duration="10 minutes",
            estimated_minutes=10,
            lessons_count=2,
            price=0,
            currency="USD",
            delivery_type="self_paced",
            is_free=True,
            certificate_enabled=False,
            published=True,
        )
        db.add(course)
        db.flush()
        module = CourseModule(
            id=uuid.uuid4(),
            course_id=course.id,
            title="Module 1",
            description="",
            order_index=1,
        )
        db.add(module)
        db.flush()
        db.add(
            Lesson(
                id=uuid.uuid4(),
                course_id=course.id,
                module_id=module.id,
                title="Lesson One",
                slug=LESSON_ONE,
                description="First lesson",
                video_provider="youtube",
                video_id="shWx3DDveg0",
                duration_seconds=69,
                order_index=1,
                published=True,
                what_you_learn=["Topic one"],
                key_concepts=["Concept one"],
                resources=[],
            )
        )
        db.add(
            Lesson(
                id=uuid.uuid4(),
                course_id=course.id,
                module_id=module.id,
                title="Lesson Two",
                slug=LESSON_TWO,
                description="Second lesson",
                video_provider="youtube",
                video_id="bhlISIxGpQo",
                duration_seconds=80,
                order_index=2,
                published=True,
                what_you_learn=["Topic two"],
                key_concepts=["Concept two"],
                resources=[],
            )
        )
        db.commit()
    finally:
        db.close()


def test_public_course_lists_curriculum_without_auth():
    _seed_course()
    response = client.get(f"/api/v1/self-paced/courses/{COURSE_SLUG}")
    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == COURSE_SLUG
    assert body["is_free"] is True
    assert body["enrolled"] is False
    assert len(body["modules"]) == 1
    assert len(body["modules"][0]["lessons"]) == 2


def test_enroll_and_lesson_access_require_auth():
    _seed_course()
    assert client.post(f"/api/v1/self-paced/courses/{COURSE_SLUG}/enroll").status_code == 401
    assert (
        client.get(f"/api/v1/self-paced/courses/{COURSE_SLUG}/lessons/{LESSON_ONE}").status_code
        == 401
    )


def test_lesson_requires_enrollment():
    _seed_course()
    user = _make_user(f"unenrolled-{uuid.uuid4()}@example.com")
    response = client.get(
        f"/api/v1/self-paced/courses/{COURSE_SLUG}/lessons/{LESSON_ONE}",
        headers=_auth(user),
    )
    assert response.status_code == 403


def test_free_enroll_is_idempotent_and_unlocks_lessons():
    _seed_course()
    user = _make_user(f"enroll-{uuid.uuid4()}@example.com")
    first = client.post(f"/api/v1/self-paced/courses/{COURSE_SLUG}/enroll", headers=_auth(user))
    second = client.post(f"/api/v1/self-paced/courses/{COURSE_SLUG}/enroll", headers=_auth(user))
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["enrollment_id"] == second.json()["enrollment_id"]
    assert second.json()["already_enrolled"] is True

    db = SessionLocal()
    try:
        count = len(
            db.scalars(
                select(Enrollment).where(
                    Enrollment.user_id == user.id,
                    Enrollment.course_id == select(Course.id).where(Course.slug == COURSE_SLUG).scalar_subquery(),
                )
            ).all()
        )
        assert count == 1
    finally:
        db.close()

    lesson = client.get(
        f"/api/v1/self-paced/courses/{COURSE_SLUG}/lessons/{LESSON_ONE}",
        headers=_auth(user),
    )
    assert lesson.status_code == 200
    assert lesson.json()["video_id"] == "shWx3DDveg0"
    assert lesson.json()["video_provider"] == "youtube"


def test_progress_is_isolated_and_completing_all_marks_course_done():
    _seed_course()
    alice = _make_user(f"alice-{uuid.uuid4()}@example.com")
    bob = _make_user(f"bob-{uuid.uuid4()}@example.com")
    client.post(f"/api/v1/self-paced/courses/{COURSE_SLUG}/enroll", headers=_auth(alice))
    client.post(f"/api/v1/self-paced/courses/{COURSE_SLUG}/enroll", headers=_auth(bob))

    complete = client.post(
        f"/api/v1/self-paced/courses/{COURSE_SLUG}/lessons/{LESSON_ONE}/complete",
        headers=_auth(alice),
    )
    assert complete.status_code == 200
    assert complete.json()["lessons_completed"] == 1
    assert complete.json()["progress_percent"] == 50
    assert complete.json()["course_completed"] is False

    bob_progress = client.get(
        f"/api/v1/self-paced/courses/{COURSE_SLUG}/progress",
        headers=_auth(bob),
    )
    assert bob_progress.json()["lessons_completed"] == 0
    assert bob_progress.json()["progress_percent"] == 0

    done = client.post(
        f"/api/v1/self-paced/courses/{COURSE_SLUG}/lessons/{LESSON_TWO}/complete",
        headers=_auth(alice),
    )
    assert done.status_code == 200
    assert done.json()["course_completed"] is True
    assert done.json()["progress_percent"] == 100

    mine = client.get("/api/v1/self-paced/me/enrollments", headers=_auth(alice))
    assert mine.status_code == 200
    row = next(item for item in mine.json() if item["course"]["slug"] == COURSE_SLUG)
    assert row["status"] == "completed"
    assert row["progress_percent"] == 100

    db = SessionLocal()
    try:
        alice_enrollment = db.scalar(
            select(Enrollment).where(Enrollment.user_id == alice.id)
        )
        bob_rows = list(
            db.scalars(
                select(LessonProgress).where(
                    LessonProgress.enrollment_id
                    == select(Enrollment.id).where(Enrollment.user_id == bob.id).scalar_subquery()
                )
            ).all()
        )
        assert alice_enrollment is not None
        assert alice_enrollment.completed_at is not None
        assert all(not row.completed for row in bob_rows)
    finally:
        db.close()


def test_admin_courses_require_admin():
    user = _make_user(f"student-admin-{uuid.uuid4()}@example.com")
    assert client.get("/api/v1/admin/courses", headers=_auth(user)).status_code == 403
    assert client.get("/api/v1/admin/courses").status_code == 401
