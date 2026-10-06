from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.live import AssignmentStatus, AttendanceStatus, ProjectStatus, SubmissionStatus
from app.core.roles import UserRole
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.attendance import Attendance
from app.models.classroom import Cohort, CohortMember, CohortMemberRole, LiveSession, LiveSessionStatus
from app.models.project import Project
from app.models.user import User
from app.schemas.reports import AtRiskStudentRow, CohortReport, GradebookRow


class CohortReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _require_instructor_access(self, user: User, cohort_id: UUID) -> None:
        if user.role in {UserRole.ADMIN, UserRole.OPERATIONS}:
            return
        member = self.db.scalar(
            select(CohortMember).where(
                CohortMember.cohort_id == cohort_id,
                CohortMember.user_id == user.id,
            )
        )
        if not member or member.role not in {CohortMemberRole.INSTRUCTOR, CohortMemberRole.TA}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an instructor for this cohort")

    def cohort_report(self, user: User, cohort_id: UUID) -> CohortReport:
        self._require_instructor_access(user, cohort_id)
        cohort = self.db.get(Cohort, cohort_id)
        if not cohort:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")

        students = list(
            self.db.scalars(
                select(CohortMember)
                .options(selectinload(CohortMember.user))
                .where(
                    CohortMember.cohort_id == cohort_id,
                    CohortMember.role == CohortMemberRole.STUDENT,
                )
            ).all()
        )
        sessions = list(
            self.db.scalars(
                select(LiveSession).where(
                    LiveSession.cohort_id == cohort_id,
                    LiveSession.status != LiveSessionStatus.CANCELLED,
                )
            ).all()
        )
        session_ids = [s.id for s in sessions]
        attendance_rows = list(
            self.db.scalars(select(Attendance).where(Attendance.session_id.in_(session_ids))).all()
        ) if session_ids else []
        assignments = list(
            self.db.scalars(
                select(Assignment).where(
                    Assignment.cohort_id == cohort_id,
                    Assignment.status == AssignmentStatus.PUBLISHED,
                )
            ).all()
        )
        assignment_ids = [a.id for a in assignments]
        submissions = list(
            self.db.scalars(
                select(AssignmentSubmission).where(AssignmentSubmission.assignment_id.in_(assignment_ids))
            ).all()
        ) if assignment_ids else []
        projects = list(
            self.db.scalars(select(Project).where(Project.cohort_id == cohort_id)).all()
        )

        attendance_by_user: dict[UUID, list[Attendance]] = {}
        for row in attendance_rows:
            attendance_by_user.setdefault(row.user_id, []).append(row)

        submissions_by_user: dict[UUID, list[AssignmentSubmission]] = {}
        for sub in submissions:
            submissions_by_user.setdefault(sub.user_id, []).append(sub)

        projects_by_user: dict[UUID, list[Project]] = {}
        for project in projects:
            projects_by_user.setdefault(project.user_id, []).append(project)

        at_risk_rows: list[AtRiskStudentRow] = []
        gradebook_rows: list[GradebookRow] = []
        for member in students:
            uid = member.user_id
            attended = sum(
                1
                for row in attendance_by_user.get(uid, [])
                if row.status in {AttendanceStatus.ATTENDED, AttendanceStatus.LATE}
            )
            missed = sum(
                1 for row in attendance_by_user.get(uid, []) if row.status == AttendanceStatus.ABSENT
            )
            own_submissions = submissions_by_user.get(uid, [])
            non_missing = [s for s in own_submissions if s.status not in {SubmissionStatus.DRAFT, SubmissionStatus.MISSING}]
            missing_assignments = max(len(assignments) - len(non_missing), 0)
            own_projects = projects_by_user.get(uid, [])
            incomplete_projects = sum(1 for p in own_projects if p.status != ProjectStatus.COMPLETED)
            at_risk = missed >= 2 or missing_assignments >= 2 or incomplete_projects >= 1
            scores = [s.score for s in non_missing if s.score is not None]
            avg_score = round(sum(scores) / len(scores), 1) if scores else None
            at_risk_rows.append(
                AtRiskStudentRow(
                    user_id=uid,
                    email=member.user.email,
                    full_name=member.user.full_name,
                    missed_sessions=missed,
                    missing_assignments=missing_assignments,
                    incomplete_projects=incomplete_projects,
                    at_risk=at_risk,
                )
            )
            gradebook_rows.append(
                GradebookRow(
                    user_id=uid,
                    full_name=member.user.full_name,
                    email=member.user.email,
                    attendance_present=attended,
                    attendance_total=len(sessions),
                    assignments_submitted=len(non_missing),
                    assignments_total=len(assignments),
                    avg_score=avg_score,
                    projects_completed=sum(
                        1 for p in own_projects if p.status == ProjectStatus.COMPLETED
                    ),
                    at_risk=at_risk,
                )
            )

        present = sum(
            1 for row in attendance_rows if row.status in {AttendanceStatus.ATTENDED, AttendanceStatus.LATE}
        )
        attendance_rate = round((present / (len(students) * len(sessions))) * 100) if students and sessions else 0
        submitted_total = sum(1 for s in submissions if s.status not in {SubmissionStatus.DRAFT, SubmissionStatus.MISSING})
        assignment_completion_rate = (
            round((submitted_total / (len(students) * len(assignments))) * 100)
            if students and assignments
            else 0
        )
        projects_completed = sum(1 for p in projects if p.status == ProjectStatus.COMPLETED)

        return CohortReport(
            cohort_id=cohort_id,
            cohort_name=cohort.name,
            student_count=len(students),
            attendance_rate=attendance_rate,
            assignment_completion_rate=assignment_completion_rate,
            projects_completed=projects_completed,
            at_risk_count=sum(1 for r in at_risk_rows if r.at_risk),
            at_risk=[r for r in at_risk_rows if r.at_risk],
            gradebook=gradebook_rows,
        )
