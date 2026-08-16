from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, get_classroom_service
from app.schemas.classroom import ClassroomJoinResponse, LiveSessionPublic, PublicCohortCard
from app.services.classroom import ClassroomService

router = APIRouter(prefix="/classroom", tags=["classroom"])


@router.get("/public/cohorts", response_model=list[PublicCohortCard])
def list_public_cohorts(
    classroom: ClassroomService = Depends(get_classroom_service),
) -> list[PublicCohortCard]:
    """Public Instructor-Led catalog (no auth)."""
    return classroom.list_public_cohorts()


@router.get("/sessions", response_model=list[LiveSessionPublic])
def list_my_sessions(
    current_user: CurrentUser,
    classroom: ClassroomService = Depends(get_classroom_service),
) -> list[LiveSessionPublic]:
    return classroom.list_my_sessions(current_user)


@router.get("/sessions/{session_id}", response_model=LiveSessionPublic)
def get_session(
    session_id: UUID,
    current_user: CurrentUser,
    classroom: ClassroomService = Depends(get_classroom_service),
) -> LiveSessionPublic:
    return classroom.get_session_for_user(current_user, session_id)


@router.post("/sessions/{session_id}/join", response_model=ClassroomJoinResponse)
def join_session(
    session_id: UUID,
    current_user: CurrentUser,
    classroom: ClassroomService = Depends(get_classroom_service),
) -> ClassroomJoinResponse:
    return classroom.join_session(current_user, session_id)
