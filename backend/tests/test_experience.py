from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.live import AttendanceStatus, ProjectStatus, SubmissionStatus
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.assignment import Assignment, AssignmentSubmission
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
from app.models.notification import Notification
from app.models.project import Project
from app.models.user import User

client = TestClient(app)

COHORT_SLUG = "test-experience-cohort"


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
            full_name="Experience Test",
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
        for n in db.scalars(select(Notification)).all():
            db.delete(n)
        cohort = db.scalar(select(Cohort).where(Cohort.slug == COHORT_SLUG))
        if cohort:
            for project in db.scalars(select(Project).where(Project.cohort_id == cohort.id)).all():
                db.delete(project)
            for sub in db.scalars(select(AssignmentSubmission)).all():
                db.delete(sub)
            for assignment in db.scalars(select(Assignment).where(Assignment.cohort_id == cohort.id)).all():
                db.delete(assignment)
            for att in db.scalars(select(Attendance)).all():
                db.delete(att)
            for member in db.scalars(select(CohortMember).where(CohortMember.cohort_id == cohort.id)).all():
                db.delete(member)
            for session in db.scalars(select(LiveSession).where(LiveSession.cohort_id == cohort.id)).all():
                db.delete(session)
            db.delete(cohort)
        for user in db.scalars(select(User).where(User.email.like("%xp-test-%@example.com"))).all():
            db.delete(user)
        db.commit()
    finally:
        db.close()


def _seed() -> tuple[uuid.UUID, uuid.UUID]:
    db = SessionLocal()
    try:
        cohort = Cohort(
            id=uuid.uuid4(),
            name="Experience Test Cohort",
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


def test_showcase_and_public_portfolio():
    _cleanup()
    cohort_id, _ = _seed()
    student = _make_user("xp-test-student")
    db = SessionLocal()
    try:
        db.add(CohortMember(cohort_id=cohort_id, user_id=student.id, role=CohortMemberRole.STUDENT))
        project = Project(
            id=uuid.uuid4(),
            cohort_id=cohort_id,
            user_id=student.id,
            title="Public Pipeline",
            status=ProjectStatus.COMPLETED,
            is_public=True,
            technologies=["Python"],
        )
        db.add(project)
        db.commit()
        project_id = str(project.id)
    finally:
        db.close()

    showcase = client.get("/api/v1/showcase/projects")
    assert showcase.status_code == 200
    assert any(p["project"]["id"] == project_id for p in showcase.json())

    # Portfolio is private by default.
    assert client.get(f"/api/v1/portfolio/{student.id}").status_code == 404

    toggled = client.patch(
        "/api/v1/me/portfolio",
        headers=_auth(student),
        json={"portfolio_public": True},
    )
    assert toggled.status_code == 200
    assert toggled.json()["portfolio_public"] is True

    public = client.get(f"/api/v1/portfolio/{student.id}")
    assert public.status_code == 200
    assert public.json()["projects"][0]["title"] == "Public Pipeline"

    _cleanup()


def test_certificate_eligibility_and_notifications():
    _cleanup()
    cohort_id, session_id = _seed()
    student = _make_user("xp-test-student")
    instructor = _make_user("xp-test-instructor", UserRole.INSTRUCTOR)
    db = SessionLocal()
    try:
        db.add(CohortMember(cohort_id=cohort_id, user_id=student.id, role=CohortMemberRole.STUDENT))
        db.add(CohortMember(cohort_id=cohort_id, user_id=instructor.id, role=CohortMemberRole.INSTRUCTOR))
        db.add(Attendance(session_id=session_id, user_id=student.id, status=AttendanceStatus.ATTENDED))
        assignment = Assignment(
            id=uuid.uuid4(),
            cohort_id=cohort_id,
            title="Eligibility assignment",
            status="published",
        )
        db.add(assignment)
        db.flush()
        db.add(AssignmentSubmission(
            id=uuid.uuid4(),
            assignment_id=assignment.id,
            user_id=student.id,
            status=SubmissionStatus.SUBMITTED,
        ))
        db.add(Project(
            id=uuid.uuid4(),
            cohort_id=cohort_id,
            user_id=student.id,
            title="Completed project",
            status=ProjectStatus.COMPLETED,
        ))
        db.commit()
    finally:
        db.close()

    eligibility = client.get("/api/v1/me/certificate-eligibility", headers=_auth(student))
    assert eligibility.status_code == 200
    assert eligibility.json()[0]["eligible"] is True

    created = client.post(
        "/api/v1/instructor/assignments",
        headers=_auth(instructor),
        json={"cohort_id": str(cohort_id), "title": "Notif assignment", "status": "published"},
    )
    assignment_id = created.json()["id"]
    sub = client.put(
        f"/api/v1/assignments/{assignment_id}/submissions/me",
        headers=_auth(student),
        json={"status": "submitted", "text_response": "done"},
    )
    submission_id = sub.json()["id"]
    client.patch(
        f"/api/v1/instructor/submissions/{submission_id}/review",
        headers=_auth(instructor),
        json={"score": 90, "feedback": "Nice work", "status": "reviewed"},
    )

    notes = client.get("/api/v1/me/notifications", headers=_auth(student))
    assert notes.status_code == 200
    assert notes.json()[0]["title"] == "Assignment reviewed"

    read = client.post("/api/v1/me/notifications/read-all", headers=_auth(student))
    assert read.status_code == 200
    assert read.json()["unread"] == 0

    _cleanup()
