from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, get_assignment_service, require_instructor
from app.models.user import User
from app.schemas.assignments import (
    AssignmentDetailPublic,
    AssignmentPublic,
    AssignmentTrackingPublic,
    AssignmentUpsert,
    ReviewSubmissionRequest,
    SubmissionPublic,
    SubmissionUpsert,
)
from app.services.assignments import AssignmentService

router = APIRouter(tags=["assignments"])


@router.get("/cohorts/{cohort_id}/assignments", response_model=list[AssignmentPublic])
def my_assignments(
    cohort_id: UUID,
    current_user: CurrentUser,
    assignments: AssignmentService = Depends(get_assignment_service),
) -> list[AssignmentPublic]:
    return assignments.list_assignments(current_user, cohort_id)


@router.get("/assignments/{assignment_id}", response_model=AssignmentDetailPublic)
def get_assignment(
    assignment_id: UUID,
    current_user: CurrentUser,
    assignments: AssignmentService = Depends(get_assignment_service),
) -> AssignmentDetailPublic:
    return assignments.get_assignment(current_user, assignment_id)


@router.put("/assignments/{assignment_id}/submissions/me", response_model=SubmissionPublic)
def upsert_my_submission(
    assignment_id: UUID,
    payload: SubmissionUpsert,
    current_user: CurrentUser,
    assignments: AssignmentService = Depends(get_assignment_service),
) -> SubmissionPublic:
    return assignments.upsert_submission(current_user, assignment_id, payload)


@router.get("/instructor/cohorts/{cohort_id}/assignments", response_model=list[AssignmentPublic])
def instructor_assignments(
    cohort_id: UUID,
    current_user: User = Depends(require_instructor),
    assignments: AssignmentService = Depends(get_assignment_service),
) -> list[AssignmentPublic]:
    return assignments.list_cohort_assignments(current_user, cohort_id)


@router.post("/instructor/assignments", response_model=AssignmentPublic, status_code=201)
def create_assignment(
    payload: AssignmentUpsert,
    current_user: User = Depends(require_instructor),
    assignments: AssignmentService = Depends(get_assignment_service),
) -> AssignmentPublic:
    return assignments.create_assignment(current_user, payload)


@router.patch("/instructor/assignments/{assignment_id}", response_model=AssignmentPublic)
def update_assignment(
    assignment_id: UUID,
    payload: AssignmentUpsert,
    current_user: User = Depends(require_instructor),
    assignments: AssignmentService = Depends(get_assignment_service),
) -> AssignmentPublic:
    return assignments.update_assignment(current_user, assignment_id, payload)


@router.get("/instructor/assignments/{assignment_id}/tracking", response_model=AssignmentTrackingPublic)
def assignment_tracking(
    assignment_id: UUID,
    current_user: User = Depends(require_instructor),
    assignments: AssignmentService = Depends(get_assignment_service),
) -> AssignmentTrackingPublic:
    return assignments.get_assignment_tracking(current_user, assignment_id)


@router.patch("/instructor/submissions/{submission_id}/review", response_model=SubmissionPublic)
def review_submission(
    submission_id: UUID,
    payload: ReviewSubmissionRequest,
    current_user: User = Depends(require_instructor),
    assignments: AssignmentService = Depends(get_assignment_service),
) -> SubmissionPublic:
    return assignments.review_submission(current_user, submission_id, payload)
