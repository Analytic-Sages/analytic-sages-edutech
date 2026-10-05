from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, get_project_service, require_instructor
from app.models.user import User
from app.schemas.projects import (
    InstructorProjectRow,
    ProjectPublic,
    ProjectUpsert,
    ReviewProjectRequest,
)
from app.services.projects import ProjectService

router = APIRouter(tags=["projects"])


@router.get("/cohorts/{cohort_id}/projects", response_model=list[ProjectPublic])
def my_projects(
    cohort_id: UUID,
    current_user: CurrentUser,
    projects: ProjectService = Depends(get_project_service),
) -> list[ProjectPublic]:
    return projects.list_my_projects(current_user, cohort_id)


@router.post("/cohorts/{cohort_id}/projects", response_model=ProjectPublic, status_code=201)
def create_project(
    cohort_id: UUID,
    payload: ProjectUpsert,
    current_user: CurrentUser,
    projects: ProjectService = Depends(get_project_service),
) -> ProjectPublic:
    return projects.upsert_project(current_user, cohort_id, payload)


@router.put("/projects/{project_id}", response_model=ProjectPublic)
def update_project(
    project_id: UUID,
    payload: ProjectUpsert,
    current_user: CurrentUser,
    projects: ProjectService = Depends(get_project_service),
) -> ProjectPublic:
    return projects.update_project(current_user, project_id, payload)


@router.get("/instructor/cohorts/{cohort_id}/projects", response_model=list[InstructorProjectRow])
def instructor_projects(
    cohort_id: UUID,
    current_user: User = Depends(require_instructor),
    projects: ProjectService = Depends(get_project_service),
) -> list[InstructorProjectRow]:
    return projects.list_cohort_projects(current_user, cohort_id)


@router.patch("/instructor/projects/{project_id}/review", response_model=ProjectPublic)
def review_project(
    project_id: UUID,
    payload: ReviewProjectRequest,
    current_user: User = Depends(require_instructor),
    projects: ProjectService = Depends(get_project_service),
) -> ProjectPublic:
    return projects.review_project(current_user, project_id, payload)
