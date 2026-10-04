from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.payments import EnrollmentStatus
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import User

client = TestClient(app)

SLUG_PREFIX = "quiz-test"


def _token_for(user: User) -> str:
    return SecurityService(get_settings()).create_access_token(
        user_id=str(user.id), role=user.role.value
    )


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_for(user)}"}


def _make_user(role: UserRole = UserRole.STUDENT) -> User:
    db = SessionLocal()
    try:
        user = User(
            email=f"quiz-test-{uuid.uuid4().hex[:8]}@example.com",
            full_name="Quiz Taker",
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
        courses = db.scalars(select(Course).where(Course.slug.like(f"{SLUG_PREFIX}%"))).all()
        course_ids = [course.id for course in courses]
        users = db.scalars(select(User).where(User.email.like("quiz-test-%@example.com"))).all()
        user_ids = [user.id for user in users]
        if course_ids or user_ids:
            for enrollment in db.scalars(
                select(Enrollment).where(
                    Enrollment.course_id.in_(course_ids) | Enrollment.user_id.in_(user_ids)
                )
            ).all():
                db.delete(enrollment)
            db.flush()
        for course in courses:
            db.delete(course)
        for user in users:
            db.delete(user)
        db.commit()
    finally:
        db.close()


def _seed_course_with_quiz(admin: User) -> tuple[str, str]:
    """Create a published free course with one module + one 2-question quiz."""
    slug = f"{SLUG_PREFIX}-{uuid.uuid4().hex[:6]}"
    client.post(
        "/api/v1/admin/courses",
        headers=_auth(admin),
        json={"slug": slug, "title": "Quiz Course", "price": 0, "is_free": True, "published": True},
    )
    module = client.post(
        f"/api/v1/admin/courses/{slug}/modules",
        headers=_auth(admin),
        json={"title": "Module 1"},
    ).json()
    # A published lesson so the public course endpoint treats it as live.
    client.post(
        f"/api/v1/admin/modules/{module['id']}/lessons",
        headers=_auth(admin),
        json={"title": "Lesson 1", "published": True},
    )
    quiz = client.post(
        f"/api/v1/admin/courses/{slug}/quizzes",
        headers=_auth(admin),
        json={"title": "Module 1 Quiz", "pass_score": 50, "module_id": module["id"]},
    ).json()
    # Question 1
    client.post(
        f"/api/v1/admin/quizzes/{quiz['id']}/questions",
        headers=_auth(admin),
        json={
            "prompt": "What is a block hash for?",
            "explanation": "It links blocks and verifies integrity.",
            "options": [
                {"label": "Storing passwords", "is_correct": False},
                {"label": "Linking blocks", "is_correct": True},
            ],
        },
    )
    # Question 2
    client.post(
        f"/api/v1/admin/quizzes/{quiz['id']}/questions",
        headers=_auth(admin),
        json={
            "prompt": "Which tool explores Ethereum transactions?",
            "options": [
                {"label": "Etherscan", "is_correct": True},
                {"label": "Photoshop", "is_correct": False},
            ],
        },
    )
    detail = client.get(f"/api/v1/admin/quizzes/{quiz['id']}", headers=_auth(admin)).json()
    return slug, detail["id"]


def _enroll(user: User, slug: str) -> None:
    db = SessionLocal()
    try:
        course = db.scalar(select(Course).where(Course.slug == slug))
        db.add(
            Enrollment(
                user_id=user.id,
                course_id=course.id,
                status=EnrollmentStatus.ACTIVE,
            )
        )
        db.commit()
    finally:
        db.close()


@pytest.fixture
def quiz_env():
    _cleanup()
    admin = _make_user(UserRole.ADMIN)
    slug, quiz_id = _seed_course_with_quiz(admin)
    yield {"admin": admin, "slug": slug, "quiz_id": quiz_id}
def test_learner_quiz_view_hides_answers(quiz_env):
    student = _make_user()
    _enroll(student, quiz_env["slug"])
    try:
        response = client.get(f"/api/v1/quizzes/{quiz_env['quiz_id']}", headers=_auth(student))
        assert response.status_code == 200
        body = response.json()
        assert body["questions_total"] == 2
        assert body["pass_score"] == 50
        # No correct-answer data leaks.
        raw = response.text
        assert "is_correct" not in raw
        for question in body["questions"]:
            for option in question["options"]:
                assert set(option.keys()) == {"id", "label"}
    finally:
        _cleanup()


def test_quiz_requires_enrollment(quiz_env):
    outsider = _make_user()
    try:
        response = client.get(f"/api/v1/quizzes/{quiz_env['quiz_id']}", headers=_auth(outsider))
        assert response.status_code == 403
    finally:
        _cleanup()


def test_submit_quiz_grades_server_side(quiz_env):
    student = _make_user()
    _enroll(student, quiz_env["slug"])
    try:
        quiz = client.get(
            f"/api/v1/quizzes/{quiz_env['quiz_id']}", headers=_auth(student)
        ).json()
        # Choose all-correct answers.
        answers = []
        for question in quiz["questions"]:
            correct_label = (
                "Linking blocks"
                if question["prompt"].startswith("What is a block hash")
                else "Etherscan"
            )
            option = next(o for o in question["options"] if o["label"] == correct_label)
            answers.append({"question_id": question["id"], "option_id": option["id"]})

        result = client.post(
            f"/api/v1/quizzes/{quiz_env['quiz_id']}/submit",
            headers=_auth(student),
            json={"answers": answers},
        )
        assert result.status_code == 200, result.text
        body = result.json()
        assert body["score"] == 100
        assert body["passed"] is True
        assert body["correct_count"] == 2

        # A wrong attempt lowers the score.
        wrong = []
        for question in quiz["questions"]:
            wrong.append({"question_id": question["id"], "option_id": question["options"][1]["id"]})
        second = client.post(
            f"/api/v1/quizzes/{quiz_env['quiz_id']}/submit",
            headers=_auth(student),
            json={"answers": wrong},
        ).json()
        assert second["score"] < 100

        # Best score sticks on the quiz view.
        refreshed = client.get(
            f"/api/v1/quizzes/{quiz_env['quiz_id']}", headers=_auth(student)
        ).json()
        assert refreshed["best_score"] == 100
        assert refreshed["passed"] is True
        assert refreshed["attempts_count"] == 2
    finally:
        _cleanup()


def test_course_quiz_listing(quiz_env):
    student = _make_user()
    _enroll(student, quiz_env["slug"])
    try:
        response = client.get(
            f"/api/v1/quizzes/course/{quiz_env['slug']}", headers=_auth(student)
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "Module 1 Quiz"
    finally:
        _cleanup()


def test_admin_quiz_requires_staff(quiz_env):
    student = _make_user()
    try:
        assert (
            client.get(
                f"/api/v1/admin/quizzes/{quiz_env['quiz_id']}", headers=_auth(student)
            ).status_code
            == 403
        )
    finally:
        _cleanup()


def test_learn_outline_includes_module_quiz(quiz_env):
    student = _make_user()
    _enroll(student, quiz_env["slug"])
    try:
        response = client.get(
            f"/api/v1/self-paced/courses/{quiz_env['slug']}/learn", headers=_auth(student)
        )
        assert response.status_code == 200, response.text
        modules = response.json()["modules"]
        assert modules, "expected at least one module"
        quiz = modules[0]["quiz"]
        assert quiz is not None
        assert quiz["title"] == "Module 1 Quiz"
        assert quiz["questions_total"] == 2
        assert quiz["id"] == quiz_env["quiz_id"]
    finally:
        _cleanup()


def test_admin_quiz_listing_and_detail(quiz_env):
    admin = quiz_env["admin"]
    try:
        listing = client.get(
            f"/api/v1/admin/quizzes?course_slug={quiz_env['slug']}", headers=_auth(admin)
        )
        assert listing.status_code == 200
        rows = listing.json()
        assert len(rows) == 1
        assert rows[0]["questions_total"] == 2

        detail = client.get(
            f"/api/v1/admin/quizzes/{quiz_env['quiz_id']}", headers=_auth(admin)
        ).json()
        # Admins see answer keys.
        assert detail["questions"][0]["options"][0]["is_correct"] in (True, False)
        assert any(option["is_correct"] for option in detail["questions"][0]["options"])
    finally:
        pass


def test_admin_question_requires_a_correct_option(quiz_env):
    response = client.post(
        f"/api/v1/admin/quizzes/{quiz_env['quiz_id']}/questions",
        headers=_auth(quiz_env["admin"]),
        json={
            "prompt": "No correct answer",
            "options": [
                {"label": "A", "is_correct": False},
                {"label": "B", "is_correct": False},
            ],
        },
    )
    assert response.status_code == 400
    _cleanup()