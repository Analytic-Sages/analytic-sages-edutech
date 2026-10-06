from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.live import AssignmentStatus, AttendanceStatus, ProjectStatus, SubmissionStatus
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
from app.models.project import Project
from app.models.user import User

client = TestClient(app)

COHORT_SLUG = "test-projects-cohort"


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
            full_name="Projects Test",
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
            for project in db.scalars(select(Project).where(Project.cohort_id == cohort.id)).all():
                db.delete(project)
            for member in db.scalars(select(CohortMember).where(CohortMember.cohort_id == cohort.id)).all():
                db.delete(member)
            for session in db.scalars(select(LiveSession).where(LiveSession.cohort_id == cohort.id)).all():
                db.delete(session)
            db.delete(cohort)
        for user in db.scalars(select(User).where(User.email.like("%proj-test-%@example.com"))).all():
            db.delete(user)
        db.commit()
    finally:
        db.close()


def _seed() -> tuple[uuid.UUID, uuid.UUID]:
    db = SessionLocal()
    try:
        cohort = Cohort(
            id=uuid.uuid4(),
            name="Projects Test Cohort",
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


def test_student_project_and_instructor_review():
    _cleanup()
    cohort_id, _ = _seed()
    student = _make_user("proj-test-student")
    instructor = _make_user("proj-test-instructor", UserRole.INSTRUCTOR)
    db = SessionLocal()
    try:
        db.add(CohortMember(cohort_id=cohort_id, user_id=student.id, role=CohortMemberRole.STUDENT))
        db.add(CohortMember(cohort_id=cohort_id, user_id=instructor.id, role=CohortMemberRole.INSTRUCTOR))
        db.commit()
    finally:
        db.close()

    created = client.post(
        f"/api/v1/cohorts/{cohort_id}/projects",
        headers=_auth(student),
        json={
            "title": "Morpho Analytics Pipeline",
            "description": "Extract and model Morpho data",
            "status": "in_progress",
            "github_url": "https://github.com/me/morpho",
            "technologies": ["Python", "SQL", "dbt"],
            "is_public": False,
        },
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    mine = client.get(f"/api/v1/cohorts/{cohort_id}/projects", headers=_auth(student))
    assert mine.status_code == 200
    assert mine.json()[0]["id"] == project_id

    listed = client.get(f"/api/v1/instructor/cohorts/{cohort_id}/projects", headers=_auth(instructor))
    assert listed.status_code == 200
    assert listed.json()[0]["project"]["title"] == "Morpho Analytics Pipeline"

    reviewed = client.patch(
        f"/api/v1/instructor/projects/{project_id}/review",
        headers=_auth(instructor),
        json={"feedback": "Great pipeline.", "status": "completed"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "completed"
    assert reviewed.json()["feedback"] == "Great pipeline."

    _cleanup()


def test_project_ownership_and_instructor_scope():
    _cleanup()
    cohort_id, _ = _seed()
    student = _make_user("proj-test-student")
    stranger = _make_user("proj-test-stranger")
    instructor = _make_user("proj-test-instructor", UserRole.INSTRUCTOR)
    outsider = _make_user("proj-test-outside-instructor", UserRole.INSTRUCTOR)
    db = SessionLocal()
    try:
        db.add(CohortMember(cohort_id=cohort_id, user_id=student.id, role=CohortMemberRole.STUDENT))
        db.add(CohortMember(cohort_id=cohort_id, user_id=instructor.id, role=CohortMemberRole.INSTRUCTOR))
        db.commit()
    finally:
        db.close()

    created = client.post(
        f"/api/v1/cohorts/{cohort_id}/projects",
        headers=_auth(student),
        json={"title": "Owned project", "status": "planned"},
    )
    project_id = created.json()["id"]

    assert client.put(
        f"/api/v1/projects/{project_id}",
        headers=_auth(stranger),
        json={"title": "Stolen", "status": "completed"},
    ).status_code == 404

    assert client.get(
        f"/api/v1/instructor/cohorts/{cohort_id}/projects", headers=_auth(outsider)
    ).status_code == 403

    _cleanup()


def test_cohort_report_flags_at_risk():
    _cleanup()
    cohort_id, session_id = _seed()
    student_a = _make_user("proj-test-a")
    student_b = _make_user("proj-test-b")
    instructor = _make_user("proj-test-instructor", UserRole.INSTRUCTOR)
    db = SessionLocal()
    try:
        db.add(CohortMember(cohort_id=cohort_id, user_id=student_a.id, role=CohortMemberRole.STUDENT))
        db.add(CohortMember(cohort_id=cohort_id, user_id=student_b.id, role=CohortMemberRole.STUDENT))
        db.add(CohortMember(cohort_id=cohort_id, user_id=instructor.id, role=CohortMemberRole.INSTRUCTOR))
        db.add(Attendance(session_id=session_id, user_id=student_a.id, status=AttendanceStatus.ABSENT))
        db.add(Attendance(session_id=session_id, user_id=student_b.id, status=AttendanceStatus.ATTENDED))
        assignment = Assignment(
            id=uuid.uuid4(),
            cohort_id=cohort_id,
            title="Report assignment",
            status=AssignmentStatus.PUBLISHED,
        )
        db.add(assignment)
        db.flush()
        db.add(AssignmentSubmission(
            id=uuid.uuid4(),
            assignment_id=assignment.id,
            user_id=student_b.id,
            status=SubmissionStatus.SUBMITTED,
        ))
        db.add(Project(
            id=uuid.uuid4(),
            cohort_id=cohort_id,
            user_id=student_a.id,
            title="Incomplete project",
            status=ProjectStatus.IN_PROGRESS,
        ))
        db.commit()
    finally:
        db.close()

    report = client.get(
        f"/api/v1/instructor/cohorts/{cohort_id}/report", headers=_auth(instructor)
    )
    assert report.status_code == 200
    data = report.json()
    assert data["student_count"] == 2
    assert data["at_risk_count"] == 1
    assert data["at_risk"][0]["email"] == student_a.email

    # Gradebook: one row per student with attendance + assignment rollups.
    gradebook = {row["email"]: row for row in data["gradebook"]}
    assert set(gradebook) == {student_a.email, student_b.email}
    assert gradebook[student_a.email]["attendance_present"] == 0
    assert gradebook[student_a.email]["at_risk"] is True
    assert gradebook[student_b.email]["attendance_present"] == 1
    assert gradebook[student_b.email]["assignments_submitted"] == 1
    assert gradebook[student_b.email]["assignments_total"] == 1

    # Admin can read the same report (supervising staff performance review).
    admin = _make_user("proj-test-admin", UserRole.ADMIN)
    admin_report = client.get(
        f"/api/v1/instructor/cohorts/{cohort_id}/report", headers=_auth(admin)
    )
    assert admin_report.status_code == 200
    assert admin_report.json()["student_count"] == 2
    _cleanup()
