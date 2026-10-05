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
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.classroom import (
    Cohort,
    CohortMember,
    CohortMemberRole,
    CohortStatus,
    LiveSession,
    LiveSessionStatus,
    LiveSessionType,
)
from app.models.user import User

client = TestClient(app)

COHORT_SLUG = "test-assignments-cohort"


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
            full_name="Assignments Test",
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
            for sub in db.scalars(select(AssignmentSubmission)).all():
                db.delete(sub)
            for assignment in db.scalars(select(Assignment).where(Assignment.cohort_id == cohort.id)).all():
                db.delete(assignment)
            for member in db.scalars(select(CohortMember).where(CohortMember.cohort_id == cohort.id)).all():
                db.delete(member)
            for session in db.scalars(select(LiveSession).where(LiveSession.cohort_id == cohort.id)).all():
                db.delete(session)
            db.delete(cohort)
        for user in db.scalars(select(User).where(User.email.like("%assign-test-%@example.com"))).all():
            db.delete(user)
        db.commit()
    finally:
        db.close()


def _seed() -> tuple[uuid.UUID, uuid.UUID]:
    db = SessionLocal()
    try:
        cohort = Cohort(
            id=uuid.uuid4(),
            name="Assignments Test Cohort",
            slug=COHORT_SLUG,
            description="",
            status=CohortStatus.OPEN,
        )
        db.add(cohort)
        db.flush()
        session = LiveSession(
            id=uuid.uuid4(),
            cohort_id=cohort.id,
            title="Week 1",
            week_label="Week 1",
            session_number=1,
            session_type=LiveSessionType.TEACHING,
            starts_at=datetime.now(UTC) - timedelta(days=1),
            ends_at=datetime.now(UTC) + timedelta(hours=2),
            status=LiveSessionStatus.SCHEDULED,
        )
        db.add(session)
        db.commit()
        return cohort.id, session.id
    finally:
        db.close()


def test_student_submit_and_instructor_review():
    _cleanup()
    cohort_id_uuid, _ = _seed()
    cohort_id = str(cohort_id_uuid)
    student = _make_user("assign-test-student")
    instructor = _make_user("assign-test-instructor", UserRole.INSTRUCTOR)
    db = SessionLocal()
    try:
        db.add(CohortMember(cohort_id=cohort_id_uuid, user_id=student.id, role=CohortMemberRole.STUDENT))
        db.add(CohortMember(cohort_id=cohort_id_uuid, user_id=instructor.id, role=CohortMemberRole.INSTRUCTOR))
        db.commit()
    finally:
        db.close()

    created = client.post(
        "/api/v1/instructor/assignments",
        headers=_auth(instructor),
        json={
            "cohort_id": cohort_id,
            "title": "Build a pipeline",
            "description": "Extract and load data",
            "week_label": "Week 1",
            "due_date": (datetime.now(UTC) + timedelta(days=5)).isoformat(),
            "max_score": 100,
            "required_fields": ["github_url", "build_in_public_url"],
            "status": "published",
        },
    )
    assert created.status_code == 201
    assignment_id = created.json()["id"]

    listed = client.get(f"/api/v1/cohorts/{cohort_id}/assignments", headers=_auth(student))
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == assignment_id

    submitted = client.put(
        f"/api/v1/assignments/{assignment_id}/submissions/me",
        headers=_auth(student),
        json={
            "status": "submitted",
            "text_response": "Pipeline works.",
            "github_url": "https://github.com/me/repo",
            "build_in_public_url": "https://x.com/me/status",
        },
    )
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "submitted"
    submission_id = submitted.json()["id"]

    detail = client.get(f"/api/v1/assignments/{assignment_id}", headers=_auth(student))
    assert detail.status_code == 200
    assert detail.json()["my_submission"]["status"] == "submitted"

    tracking = client.get(
        f"/api/v1/instructor/assignments/{assignment_id}/tracking", headers=_auth(instructor)
    )
    assert tracking.status_code == 200
    assert tracking.json()["submitted_count"] == 1

    reviewed = client.patch(
        f"/api/v1/instructor/submissions/{submission_id}/review",
        headers=_auth(instructor),
        json={"score": 87, "feedback": "Good work.", "status": "reviewed"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["score"] == 87

    refreshed = client.get(f"/api/v1/assignments/{assignment_id}", headers=_auth(student))
    assert refreshed.json()["my_submission"]["score"] == 87
    assert refreshed.json()["my_submission"]["feedback"] == "Good work."


def test_student_cannot_access_other_cohort_assignment():
    _cleanup()
    cohort_id_uuid, _ = _seed()
    cohort_id = str(cohort_id_uuid)
    student = _make_user("assign-test-student")
    stranger = _make_user("assign-test-stranger")
    instructor = _make_user("assign-test-instructor", UserRole.INSTRUCTOR)
    db = SessionLocal()
    try:
        db.add(CohortMember(cohort_id=cohort_id_uuid, user_id=student.id, role=CohortMemberRole.STUDENT))
        db.add(CohortMember(cohort_id=cohort_id_uuid, user_id=instructor.id, role=CohortMemberRole.INSTRUCTOR))
        db.commit()
    finally:
        db.close()

    created = client.post(
        "/api/v1/instructor/assignments",
        headers=_auth(instructor),
        json={"cohort_id": cohort_id, "title": "Restricted", "status": "published"},
    )
    assignment_id = created.json()["id"]

    assert client.get(f"/api/v1/assignments/{assignment_id}", headers=_auth(stranger)).status_code == 403
    assert client.get(f"/api/v1/assignments/{assignment_id}", headers=_auth(student)).status_code == 200
    _cleanup()


def test_unassigned_instructor_is_denied():
    _cleanup()
    cohort_id_uuid, _ = _seed()
    cohort_id = str(cohort_id_uuid)
    outsider = _make_user("assign-test-outside-instructor", UserRole.INSTRUCTOR)

    resp = client.post(
        "/api/v1/instructor/assignments",
        headers=_auth(outsider),
        json={"cohort_id": cohort_id, "title": "Nope", "status": "published"},
    )
    assert resp.status_code == 403
    _cleanup()

    _cleanup()


def test_admin_previews_cohort_assignments_without_enrollment():
    _cleanup()
    cohort_id_uuid, _ = _seed()
    cohort_id = str(cohort_id_uuid)
    instructor = _make_user("assign-test-instructor", UserRole.INSTRUCTOR)
    admin = _make_user("assign-test-admin", UserRole.ADMIN)
    db = SessionLocal()
    try:
        db.add(
            CohortMember(
                cohort_id=cohort_id_uuid, user_id=instructor.id, role=CohortMemberRole.INSTRUCTOR
            )
        )
        db.commit()
    finally:
        db.close()

    created = client.post(
        "/api/v1/instructor/assignments",
        headers=_auth(instructor),
        json={"cohort_id": cohort_id, "title": "Preview me", "status": "published"},
    )
    assert created.status_code == 201
    assignment_id = created.json()["id"]

    # Admin has no enrollment but can still read the student assignment view.
    listed = client.get(f"/api/v1/cohorts/{cohort_id}/assignments", headers=_auth(admin))
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == assignment_id

    detail = client.get(f"/api/v1/assignments/{assignment_id}", headers=_auth(admin))
    assert detail.status_code == 200
    assert detail.json()["my_submission"] is None
    _cleanup()
