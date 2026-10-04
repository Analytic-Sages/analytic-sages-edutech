from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, get_quiz_service
from app.schemas.quizzes import (
    QuizAttemptSummary,
    QuizPublic,
    QuizResult,
    QuizSubmitRequest,
)
from app.services.quizzes import QuizService

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.get("/{quiz_id}", response_model=QuizPublic)
def get_quiz(
    quiz_id: UUID,
    current_user: CurrentUser,
    quizzes: QuizService = Depends(get_quiz_service),
) -> QuizPublic:
    """Fetch a quiz to take. Never includes the correct answers."""
    return quizzes.get_quiz_for_user(current_user, quiz_id)


@router.post("/{quiz_id}/submit", response_model=QuizResult)
def submit_quiz(
    quiz_id: UUID,
    payload: QuizSubmitRequest,
    current_user: CurrentUser,
    quizzes: QuizService = Depends(get_quiz_service),
) -> QuizResult:
    """Grade a submission server-side and record an attempt."""
    return quizzes.submit_attempt(current_user, quiz_id, payload.answers)


@router.get("/{quiz_id}/attempts", response_model=list[QuizAttemptSummary])
def list_my_quiz_attempts(
    quiz_id: UUID,
    current_user: CurrentUser,
    quizzes: QuizService = Depends(get_quiz_service),
) -> list[QuizAttemptSummary]:
    return quizzes.list_my_attempts(current_user, quiz_id)


@router.get("/course/{course_slug}", response_model=list[QuizPublic])
def list_course_quizzes(
    course_slug: str,
    current_user: CurrentUser,
    quizzes: QuizService = Depends(get_quiz_service),
) -> list[QuizPublic]:
    """All published quizzes for a course (with my best score)."""
    return quizzes.list_quizzes_for_course(current_user, course_slug)