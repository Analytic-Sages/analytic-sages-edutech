from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.classroom import Cohort, CohortStatus
from app.models.course import Course
from app.models.instructor import InstructorProfile
from app.models.lms import CourseModule, Lesson
from app.models.user import User

client = TestClient(app)

COURSE_SLUG = "test-instructor-course"
COHORT_SLUG = "test-instructor-cohort"


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
            full_name="Test User",
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
            db.delete(cohort)
        course = db.scalar(select(Course).where(Course.slug == COURSE_SLUG))
        if course:
            db.delete(course)
        for profile in db.scalars(select(InstructorProfile).where(InstructorProfile.name.like("Test Instructor%"))).all():
            db.delete(profile)
        db.commit()
    finally:
        db.close()


def _seed_course() -> Course:
    db = SessionLocal()
    try:
        existing = db.scalar(select(Course).where(Course.slug == COURSE_SLUG))
        if existing:
            existing.published = True
            existing.is_free = True
            db.commit()
            db.refresh(existing)
            return existing
        course = Course(
            id=uuid.uuid4(),
            slug=COURSE_SLUG,
            title="Test Instructor Course",
            description="Course used to test instructor assignment.",
            long_description="Course used to test instructor assignment.",
            category="Blockchain",
            difficulty="Beginner",
            duration="10 minutes",
            estimated_minutes=10,
            lessons_count=1,
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
                title="Lesson one",
                slug="lesson-one",
                description="",
                video_provider="youtube",
                video_id="abc",
                duration_seconds=60,
                order_index=1,
                published=True,
            )
        )
        db.commit()
        db.refresh(course)
        return course
    finally:
        db.close()


def _seed_cohort(course_id) -> None:
    db = SessionLocal()
    try:
        existing = db.scalar(select(Cohort).where(Cohort.slug == COHORT_SLUG))
        if existing:
            return
        db.add(
            Cohort(
                id=uuid.uuid4(),
                course_id=course_id,
                name="Test Instructor Cohort",
                slug=COHORT_SLUG,
                description="For instructor tests",
                status=CohortStatus.OPEN,
                price=35000,
                currency="NGN",
            )
        )
        db.commit()
    finally:
        db.close()


def test_operations_can_assign_instructors_student_cannot():
    _cleanup()
    course = _seed_course()
    _seed_cohort(course.id)
    ops = _make_user(f"ops-instructors-{uuid.uuid4()}@example.com", role=UserRole.OPERATIONS)
    student = _make_user(f"student-instructors-{uuid.uuid4()}@example.com")

    assert client.get("/api/v1/admin/courses", headers=_auth(student)).status_code == 403
    listed = client.get("/api/v1/admin/courses", headers=_auth(ops))
    assert listed.status_code == 200

    created = client.post(
        "/api/v1/admin/instructor-profiles",
        headers=_auth(ops),
        json={
            "name": "Test Instructor Ada",
            "title": "Onchain analyst",
            "photo_url": "/instructors/ada.jpg",
            "bullets": ["Teaches SQL", "Builds Dune dashboards"],
        },
    )
    assert created.status_code == 201
    instructor_id = created.json()["id"]

    assigned = client.put(
        f"/api/v1/admin/courses/{COURSE_SLUG}/instructors",
        headers=_auth(ops),
        json={"items": [{"instructor_id": instructor_id, "role_label": "Lead instructor", "sort_order": 0}]},
    )
    assert assigned.status_code == 200
    assert assigned.json()[0]["name"] == "Test Instructor Ada"
    assert assigned.json()[0]["role_label"] == "Lead instructor"

    public_course = client.get(f"/api/v1/self-paced/courses/{COURSE_SLUG}")
    assert public_course.status_code == 200
    people = public_course.json()["instructors"]
    assert len(people) == 1
    assert people[0]["name"] == "Test Instructor Ada"
    assert people[0]["bullets"] == ["Teaches SQL", "Builds Dune dashboards"]

    cohorts = client.get("/api/v1/classroom/public/cohorts")
    assert cohorts.status_code == 200
    match = next(item for item in cohorts.json() if item["slug"] == COHORT_SLUG)
    assert match["instructors"][0]["name"] == "Test Instructor Ada"

    second = client.post(
        "/api/v1/admin/instructor-profiles",
        headers=_auth(ops),
        json={"name": "Test Instructor Ben", "title": "Mentor", "bullets": ["Supports live class"]},
    )
    assert second.status_code == 201
    cohort_assigned = client.put(
        f"/api/v1/admin/cohorts/{COHORT_SLUG}/instructors",
        headers=_auth(ops),
        json={
            "items": [
                {"instructor_id": instructor_id, "role_label": "Lead instructor", "sort_order": 0},
                {"instructor_id": second.json()["id"], "role_label": "Co-instructor", "sort_order": 1},
            ]
        },
    )
    assert cohort_assigned.status_code == 200
    assert len(cohort_assigned.json()) == 2

    match = next(
        item for item in client.get("/api/v1/classroom/public/cohorts").json() if item["slug"] == COHORT_SLUG
    )
    assert [person["role_label"] for person in match["instructors"]] == [
        "Lead instructor",
        "Co-instructor",
    ]

    assert client.get("/api/v1/admin/users", headers=_auth(ops)).status_code == 403
    _cleanup()


def test_empty_instructors_are_an_empty_list():
    _cleanup()
    _seed_course()
    public_course = client.get(f"/api/v1/self-paced/courses/{COURSE_SLUG}")
    assert public_course.status_code == 200
    assert public_course.json()["instructors"] == []
    _cleanup()
