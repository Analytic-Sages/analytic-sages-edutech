from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, OptionalUser, get_self_paced_service
from app.schemas.self_paced import (
    CourseProgressPublic,
    EnrollResponse,
    EnrollmentWithProgress,
    LessonCompleteResponse,
    LessonDetailPublic,
    SelfPacedCourseCard,
    SelfPacedCoursePublic,
)
from app.services.self_paced import SelfPacedService

router = APIRouter(prefix="/self-paced", tags=["self-paced"])


@router.get("/courses", response_model=list[SelfPacedCourseCard])
def list_self_paced_courses(
    lms: SelfPacedService = Depends(get_self_paced_service),
) -> list[SelfPacedCourseCard]:
    return lms.list_catalog()


@router.get("/courses/{slug}", response_model=SelfPacedCoursePublic)
def get_self_paced_course(
    slug: str,
    current_user: OptionalUser,
    lms: SelfPacedService = Depends(get_self_paced_service),
) -> SelfPacedCoursePublic:
    return lms.get_public_course(slug, current_user)


@router.post("/courses/{slug}/enroll", response_model=EnrollResponse)
def enroll_self_paced_course(
    slug: str,
    current_user: CurrentUser,
    lms: SelfPacedService = Depends(get_self_paced_service),
) -> EnrollResponse:
    return lms.enroll_free(current_user, slug)


@router.get("/courses/{slug}/learn", response_model=SelfPacedCoursePublic)
def get_self_paced_learn(
    slug: str,
    current_user: CurrentUser,
    lms: SelfPacedService = Depends(get_self_paced_service),
) -> SelfPacedCoursePublic:
    return lms.get_learn_course(current_user, slug)


@router.get("/courses/{slug}/progress", response_model=CourseProgressPublic)
def get_self_paced_progress(
    slug: str,
    current_user: CurrentUser,
    lms: SelfPacedService = Depends(get_self_paced_service),
) -> CourseProgressPublic:
    return lms.get_progress(current_user, slug)


@router.get("/courses/{slug}/lessons/{lesson_slug}", response_model=LessonDetailPublic)
def get_self_paced_lesson(
    slug: str,
    lesson_slug: str,
    current_user: CurrentUser,
    lms: SelfPacedService = Depends(get_self_paced_service),
) -> LessonDetailPublic:
    return lms.get_lesson(current_user, slug, lesson_slug)


@router.post(
    "/courses/{slug}/lessons/{lesson_slug}/complete",
    response_model=LessonCompleteResponse,
)
def complete_self_paced_lesson(
    slug: str,
    lesson_slug: str,
    current_user: CurrentUser,
    lms: SelfPacedService = Depends(get_self_paced_service),
) -> LessonCompleteResponse:
    return lms.complete_lesson(current_user, slug, lesson_slug)


@router.get("/me/enrollments", response_model=list[EnrollmentWithProgress])
def my_self_paced_enrollments(
    current_user: CurrentUser,
    lms: SelfPacedService = Depends(get_self_paced_service),
) -> list[EnrollmentWithProgress]:
    return lms.list_my_enrollments(current_user)
