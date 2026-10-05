from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.live import AssignmentStatus, AttendanceStatus, ProjectStatus, SubmissionStatus
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.attendance import Attendance
from app.models.classroom import Cohort, CohortMember, CohortMemberRole, LiveSession, LiveSessionStatus
from app.models.project import Project
from app.models.user import User
from app.schemas.certificates import CertificateEligibilityPublic

DEFAULT_REQUIREMENTS: dict[str, Any] = {
    "min_attendance_percent": 60,
    "require_all_assignments": True,
    "require_project": True,
}


class CertificateService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def eligibility_for_user(self, user: User) -> list[CertificateEligibilityPublic]:
        memberships = list(
            self.db.scalars(
                select(CohortMember)
                .options(selectinload(CohortMember.cohort).joinedload(Cohort.programme))
                .where(
                    CohortMember.user_id == user.id,
                    CohortMember.role == CohortMemberRole.STUDENT,
                )
            ).all()
        )
        results: list[CertificateEligibilityPublic] = []
        for member in memberships:
            cohort = member.cohort
            results.append(self._eligibility_for_cohort(user.id, cohort))
        return results

    def _eligibility_for_cohort(self, user_id: UUID, cohort) -> CertificateEligibilityPublic:
        sessions = list(
            self.db.scalars(
                select(LiveSession).where(
                    LiveSession.cohort_id == cohort.id,
                    LiveSession.status != LiveSessionStatus.CANCELLED,
                )
            ).all()
        )
        session_ids = [s.id for s in sessions]
        attendance_rows = (
            list(
                self.db.scalars(
                    select(Attendance).where(
                        Attendance.user_id == user_id,
                        Attendance.session_id.in_(session_ids),
                    )
                ).all()
            )
            if session_ids
            else []
        )
        present = sum(
            1 for r in attendance_rows if r.status in {AttendanceStatus.ATTENDED, AttendanceStatus.LATE}
        )
        attendance_percent = round((present / len(sessions)) * 100) if sessions else 0

        assignments = list(
            self.db.scalars(
                select(Assignment).where(
                    Assignment.cohort_id == cohort.id,
                    Assignment.status == AssignmentStatus.PUBLISHED,
                )
            ).all()
        )
        assignment_ids = [a.id for a in assignments]
        submissions = (
            list(
                self.db.scalars(
                    select(AssignmentSubmission).where(
                        AssignmentSubmission.user_id == user_id,
                        AssignmentSubmission.assignment_id.in_(assignment_ids),
                    )
                ).all()
            )
            if assignment_ids
            else []
        )
        submitted = [
            s for s in submissions if s.status not in {SubmissionStatus.DRAFT, SubmissionStatus.MISSING}
        ]
        projects = list(
            self.db.scalars(
                select(Project).where(Project.cohort_id == cohort.id, Project.user_id == user_id)
            ).all()
        )
        projects_completed = sum(1 for p in projects if p.status == ProjectStatus.COMPLETED)

        requirements: dict[str, Any] = dict(DEFAULT_REQUIREMENTS)
        if cohort.programme and cohort.programme.certificate_requirements:
            requirements.update(cohort.programme.certificate_requirements or {})

        eligible = True
        if sessions and attendance_percent < int(requirements.get("min_attendance_percent", 60)):
            eligible = False
        if assignments:
            if requirements.get("require_all_assignments", True):
                if len(submitted) < len(assignments):
                    eligible = False
            elif int(requirements.get("min_assignments_submitted", 0)) > len(submitted):
                eligible = False
        if requirements.get("require_project", True) and projects_completed < 1:
            eligible = False

        return CertificateEligibilityPublic(
            cohort_id=cohort.id,
            cohort_name=cohort.name,
            programme_slug=cohort.programme.slug if cohort.programme else None,
            programme_title=cohort.programme.title if cohort.programme else None,
            eligible=eligible,
            attendance_percent=attendance_percent,
            assignments_submitted=len(submitted),
            assignments_total=len(assignments),
            projects_completed=projects_completed,
            requirements=requirements,
        )
