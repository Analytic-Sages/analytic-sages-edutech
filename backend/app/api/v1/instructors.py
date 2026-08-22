from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import get_instructor_service, require_catalog_ops
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.instructors import (
    AdminCohortInstructorRow,
    InstructorAssignmentWrite,
    InstructorProfileAdmin,
    InstructorProfileWrite,
    InstructorPublic,
)
from app.services.instructors import InstructorService

router = APIRouter(tags=["instructors"])


@router.get("/admin/instructor-profiles", response_model=list[InstructorProfileAdmin])
def list_instructor_profiles(
    _: User = Depends(require_catalog_ops),
    instructors: InstructorService = Depends(get_instructor_service),
) -> list[InstructorProfileAdmin]:
    return instructors.list_profiles()


@router.post(
    "/admin/instructor-profiles",
    response_model=InstructorProfileAdmin,
    status_code=status.HTTP_201_CREATED,
)
def create_instructor_profile(
    payload: InstructorProfileWrite,
    _: User = Depends(require_catalog_ops),
    instructors: InstructorService = Depends(get_instructor_service),
) -> InstructorProfileAdmin:
    return instructors.create_profile(payload)


@router.patch("/admin/instructor-profiles/{instructor_id}", response_model=InstructorProfileAdmin)
def update_instructor_profile(
    instructor_id: UUID,
    payload: InstructorProfileWrite,
    _: User = Depends(require_catalog_ops),
    instructors: InstructorService = Depends(get_instructor_service),
) -> InstructorProfileAdmin:
    return instructors.update_profile(instructor_id, payload)


@router.delete("/admin/instructor-profiles/{instructor_id}", response_model=MessageResponse)
def delete_instructor_profile(
    instructor_id: UUID,
    _: User = Depends(require_catalog_ops),
    instructors: InstructorService = Depends(get_instructor_service),
) -> MessageResponse:
    instructors.delete_profile(instructor_id)
    return MessageResponse(message="Instructor removed.")


@router.get("/admin/catalog/cohorts", response_model=list[AdminCohortInstructorRow])
def list_catalog_cohorts(
    _: User = Depends(require_catalog_ops),
    instructors: InstructorService = Depends(get_instructor_service),
) -> list[AdminCohortInstructorRow]:
    return instructors.list_admin_cohorts()


@router.get("/admin/courses/{slug}/instructors", response_model=list[InstructorPublic])
def list_course_instructors(
    slug: str,
    _: User = Depends(require_catalog_ops),
    instructors: InstructorService = Depends(get_instructor_service),
) -> list[InstructorPublic]:
    return instructors.list_course_assignments(slug)


@router.put("/admin/courses/{slug}/instructors", response_model=list[InstructorPublic])
def replace_course_instructors(
    slug: str,
    payload: InstructorAssignmentWrite,
    _: User = Depends(require_catalog_ops),
    instructors: InstructorService = Depends(get_instructor_service),
) -> list[InstructorPublic]:
    return instructors.replace_course_assignments(slug, payload.items)


@router.get("/admin/cohorts/{slug}/instructors", response_model=list[InstructorPublic])
def list_cohort_instructors(
    slug: str,
    _: User = Depends(require_catalog_ops),
    instructors: InstructorService = Depends(get_instructor_service),
) -> list[InstructorPublic]:
    return instructors.list_cohort_assignments(slug)


@router.put("/admin/cohorts/{slug}/instructors", response_model=list[InstructorPublic])
def replace_cohort_instructors(
    slug: str,
    payload: InstructorAssignmentWrite,
    _: User = Depends(require_catalog_ops),
    instructors: InstructorService = Depends(get_instructor_service),
) -> list[InstructorPublic]:
    return instructors.replace_cohort_assignments(slug, payload.items)
