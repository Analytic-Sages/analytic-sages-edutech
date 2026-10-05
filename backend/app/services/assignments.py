from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.live import AssignmentStatus, SubmissionStatus
from app.core.roles import UserRole
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.classroom import CohortMember, CohortMemberRole
from app.models.user import User
from app.schemas.assignments import (
    AssignmentDetailPublic,
    AssignmentPublic,
    AssignmentTrackingPublic,
    AssignmentUpsert,
    InstructorSubmissionRow,
    ReviewSubmissionRequest,
    SubmissionPublic,
    SubmissionUpsert,
)
from app.services.notifications import NotificationService


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AssignmentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_assignment(self, assignment_id: UUID) -> Assignment:
        assignment = self.db.get(Assignment, assignment_id)
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
        return assignment

    def _require_instructor_access(self, user: User, cohort_id: UUID) -> None:
        if user.role == UserRole.ADMIN:
            return
        member = self.db.scalar(
            select(CohortMember).where(
                CohortMember.cohort_id == cohort_id,
                CohortMember.user_id == user.id,
            )
        )
        if not member or member.role not in {CohortMemberRole.INSTRUCTOR, CohortMemberRole.TA}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an instructor for this cohort")

    def _require_student_enrollment(self, user: User, cohort_id: UUID) -> None:
        member = self.db.scalar(
            select(CohortMember).where(
                CohortMember.cohort_id == cohort_id,
                CohortMember.user_id == user.id,
            )
        )
        if not member or member.role != CohortMemberRole.STUDENT:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enrolled in this cohort")

    def _is_preview_staff(self, user: User) -> bool:
        """Admins/ops may read a cohort's student view (assignments, detail) read-only."""
        return user.role in {UserRole.ADMIN, UserRole.OPERATIONS}

    def _submission_public(self, sub: AssignmentSubmission) -> SubmissionPublic:
        return SubmissionPublic(
            id=sub.id,
            assignment_id=sub.assignment_id,
            user_id=sub.user_id,
            status=sub.status.value,
            text_response=sub.text_response,
            github_url=sub.github_url,
            live_url=sub.live_url,
            build_in_public_url=sub.build_in_public_url,
            documentation_url=sub.documentation_url,
            files=list(sub.files or []),
            score=sub.score,
            feedback=sub.feedback,
            reviewer_name=sub.reviewer.full_name if sub.reviewer else None,
            reviewed_at=sub.reviewed_at,
            submitted_at=sub.submitted_at,
            updated_at=sub.updated_at,
        )

    def _assignment_public(self, assignment: Assignment) -> AssignmentPublic:
        return AssignmentPublic.model_validate(assignment)

    # ---------- student ----------

    def list_assignments(self, user: User, cohort_id: UUID) -> list[AssignmentPublic]:
        if not self._is_preview_staff(user):
            self._require_student_enrollment(user, cohort_id)
        rows = list(
            self.db.scalars(
                select(Assignment)
                .where(
                    Assignment.cohort_id == cohort_id,
                    Assignment.status == AssignmentStatus.PUBLISHED,
                )
                .order_by(Assignment.due_date.asc().nulls_last())
            ).all()
        )
        return [self._assignment_public(row) for row in rows]

    def get_assignment(self, user: User, assignment_id: UUID) -> AssignmentDetailPublic:
        assignment = self._get_assignment(assignment_id)
        if not self._is_preview_staff(user):
            self._require_student_enrollment(user, assignment.cohort_id)
        sub = self.db.scalar(
            select(AssignmentSubmission).where(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.user_id == user.id,
            )
        )
        return AssignmentDetailPublic(
            **self._assignment_public(assignment).model_dump(),
            my_submission=self._submission_public(sub) if sub else None,
        )

    def upsert_submission(self, user: User, assignment_id: UUID, payload: SubmissionUpsert) -> SubmissionPublic:
        assignment = self._get_assignment(assignment_id)
        self._require_student_enrollment(user, assignment.cohort_id)

        sub = self.db.scalar(
            select(AssignmentSubmission).where(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.user_id == user.id,
            )
        )
        now = _utcnow()
        resolved_status = SubmissionStatus(payload.status)
        if payload.status == "submitted":
            due = assignment.due_date
            if due is not None:
                if due.tzinfo is None:
                    due = due.replace(tzinfo=timezone.utc)
                resolved_status = SubmissionStatus.LATE if now > due else SubmissionStatus.SUBMITTED
            else:
                resolved_status = SubmissionStatus.SUBMITTED

        if sub:
            sub.text_response = payload.text_response
            sub.github_url = payload.github_url
            sub.live_url = payload.live_url
            sub.build_in_public_url = payload.build_in_public_url
            sub.documentation_url = payload.documentation_url
            sub.files = list(payload.files)
            sub.status = resolved_status
            if payload.status == "submitted":
                sub.submitted_at = now
        else:
            sub = AssignmentSubmission(
                assignment_id=assignment_id,
                user_id=user.id,
                status=resolved_status,
                text_response=payload.text_response,
                github_url=payload.github_url,
                live_url=payload.live_url,
                build_in_public_url=payload.build_in_public_url,
                documentation_url=payload.documentation_url,
                files=list(payload.files),
                submitted_at=now if payload.status == "submitted" else None,
            )
            self.db.add(sub)

        self.db.commit()
        self.db.refresh(sub)
        return self._submission_public(sub)


    # ---------- instructor / admin ----------

    def create_assignment(self, user: User, payload: AssignmentUpsert) -> AssignmentPublic:
        self._require_instructor_access(user, payload.cohort_id)
        assignment = Assignment(
            cohort_id=payload.cohort_id,
            session_id=payload.session_id,
            title=payload.title,
            description=payload.description,
            instructions=payload.instructions,
            week_label=payload.week_label,
            due_date=payload.due_date,
            max_score=payload.max_score,
            passing_score=payload.passing_score,
            required_fields=list(payload.required_fields),
            resources=[r.model_dump() for r in payload.resources],
            status=AssignmentStatus(payload.status),
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return self._assignment_public(assignment)

    def update_assignment(self, user: User, assignment_id: UUID, payload: AssignmentUpsert) -> AssignmentPublic:
        assignment = self._get_assignment(assignment_id)
        self._require_instructor_access(user, assignment.cohort_id)
        data = payload.model_dump()
        for field in ("cohort_id", "session_id", "title", "description", "instructions", "week_label", "due_date", "max_score", "passing_score"):
            setattr(assignment, field, data[field])
        assignment.required_fields = list(data["required_fields"])
        assignment.resources = [r.model_dump() for r in payload.resources]
        assignment.status = AssignmentStatus(data["status"])
        self.db.commit()
        self.db.refresh(assignment)
        return self._assignment_public(assignment)

    def list_cohort_assignments(self, user: User, cohort_id: UUID) -> list[AssignmentPublic]:
        self._require_instructor_access(user, cohort_id)
        rows = list(
            self.db.scalars(
                select(Assignment)
                .where(Assignment.cohort_id == cohort_id)
                .order_by(Assignment.due_date.asc().nulls_last())
            ).all()
        )
        return [self._assignment_public(row) for row in rows]

    def get_assignment_tracking(self, user: User, assignment_id: UUID) -> AssignmentTrackingPublic:
        assignment = self._get_assignment(assignment_id)
        self._require_instructor_access(user, assignment.cohort_id)

        students = list(
            self.db.scalars(
                select(CohortMember)
                .options(selectinload(CohortMember.user))
                .where(
                    CohortMember.cohort_id == assignment.cohort_id,
                    CohortMember.role == CohortMemberRole.STUDENT,
                )
            ).all()
        )
        submissions = list(
            self.db.scalars(
                select(AssignmentSubmission)
                .options(selectinload(AssignmentSubmission.user), selectinload(AssignmentSubmission.reviewer))
                .where(AssignmentSubmission.assignment_id == assignment_id)
            ).all()
        )
        by_user = {s.user_id: s for s in submissions}
        non_missing = [
            s for s in submissions if s.status not in {SubmissionStatus.DRAFT, SubmissionStatus.MISSING}
        ]
        rows: list[InstructorSubmissionRow] = []
        for member in students:
            sub = by_user.get(member.user_id)
            if sub:
                rows.append(
                    InstructorSubmissionRow(
                        submission=self._submission_public(sub),
                        user_id=member.user_id,
                        email=member.user.email,
                        full_name=member.user.full_name,
                        enrollment_status=member.enrollment_status.value,
                    )
                )
            else:
                rows.append(
                    InstructorSubmissionRow(
                        submission=SubmissionPublic(
                            id=UUID(int=0),
                            assignment_id=assignment_id,
                            user_id=member.user_id,
                            status=SubmissionStatus.MISSING.value,
                        ),
                        user_id=member.user_id,
                        email=member.user.email,
                        full_name=member.user.full_name,
                        enrollment_status=member.enrollment_status.value,
                    )
                )

        return AssignmentTrackingPublic(
            **self._assignment_public(assignment).model_dump(),
            student_count=len(students),
            submitted_count=len(non_missing),
            missing_count=max(len(students) - len(non_missing), 0),
            reviewed_count=sum(1 for s in submissions if s.status == SubmissionStatus.REVIEWED),
            submissions=rows,
        )

    def review_submission(self, user: User, submission_id: UUID, payload: ReviewSubmissionRequest) -> SubmissionPublic:
        sub = self.db.scalar(
            select(AssignmentSubmission)
            .options(selectinload(AssignmentSubmission.reviewer))
            .where(AssignmentSubmission.id == submission_id)
        )
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
        assignment = self._get_assignment(sub.assignment_id)
        self._require_instructor_access(user, assignment.cohort_id)

        sub.score = payload.score
        sub.feedback = payload.feedback
        sub.status = SubmissionStatus(payload.status)
        sub.reviewed_by = user.id
        sub.reviewed_at = _utcnow()
        self.db.commit()
        self.db.refresh(sub)
        NotificationService(self.db).create(
            sub.user_id,
            type="assignment_reviewed",
            title="Assignment reviewed",
            body=(payload.feedback or "Your submission has been reviewed."),
            link=f"/assignments/{sub.assignment_id}",
        )
        return self._submission_public(sub)

