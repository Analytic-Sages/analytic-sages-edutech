from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.live import ProjectStatus
from app.core.roles import UserRole
from app.models.classroom import CohortMember, CohortMemberRole
from app.models.project import Project
from app.models.user import User
from app.schemas.projects import (
    InstructorProjectRow,
    ProjectPublic,
    ProjectUpsert,
    ReviewProjectRequest,
    ShowcaseProject,
)
from app.services.notifications import NotificationService


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db

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

    def _project_public(self, project: Project) -> ProjectPublic:
        return ProjectPublic(
            id=project.id,
            cohort_id=project.cohort_id,
            user_id=project.user_id,
            title=project.title,
            description=project.description or "",
            status=project.status.value,
            github_url=project.github_url,
            live_url=project.live_url,
            build_in_public_url=project.build_in_public_url,
            documentation_url=project.documentation_url,
            cover_image=project.cover_image,
            technologies=list(project.technologies or []),
            feedback=project.feedback,
            reviewer_name=project.reviewer.full_name if project.reviewer else None,
            reviewed_at=project.reviewed_at,
            is_public=project.is_public,
            updated_at=project.updated_at,
        )

    # ---------- student ----------

    def list_my_projects(self, user: User, cohort_id: UUID) -> list[ProjectPublic]:
        self._require_student_enrollment(user, cohort_id)
        rows = list(
            self.db.scalars(
                select(Project).where(Project.cohort_id == cohort_id, Project.user_id == user.id)
            ).all()
        )
        return [self._project_public(row) for row in rows]

    def upsert_project(self, user: User, cohort_id: UUID, payload: ProjectUpsert, project_id: UUID | None = None) -> ProjectPublic:
        self._require_student_enrollment(user, cohort_id)
        project = None
        if project_id:
            project = self.db.get(Project, project_id)
            if not project or project.user_id != user.id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        if project:
            project.title = payload.title
            project.description = payload.description
            project.status = ProjectStatus(payload.status)
            project.github_url = payload.github_url
            project.live_url = payload.live_url
            project.build_in_public_url = payload.build_in_public_url
            project.documentation_url = payload.documentation_url
            project.cover_image = payload.cover_image
            project.technologies = list(payload.technologies)
            project.is_public = payload.is_public
        else:
            project = Project(
                cohort_id=cohort_id,
                user_id=user.id,
                title=payload.title,
                description=payload.description,
                status=ProjectStatus(payload.status),
                github_url=payload.github_url,
                live_url=payload.live_url,
                build_in_public_url=payload.build_in_public_url,
                documentation_url=payload.documentation_url,
                cover_image=payload.cover_image,
                technologies=list(payload.technologies),
                is_public=payload.is_public,
            )
            self.db.add(project)

        self.db.commit()
        self.db.refresh(project)
        return self._project_public(project)

    def update_project(self, user: User, project_id: UUID, payload: ProjectUpsert) -> ProjectPublic:
        project = self.db.get(Project, project_id)
        if not project or project.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        self._require_student_enrollment(user, project.cohort_id)
        project.title = payload.title
        project.description = payload.description
        project.status = ProjectStatus(payload.status)
        project.github_url = payload.github_url
        project.live_url = payload.live_url
        project.build_in_public_url = payload.build_in_public_url
        project.documentation_url = payload.documentation_url
        project.cover_image = payload.cover_image
        project.technologies = list(payload.technologies)
        project.is_public = payload.is_public
        self.db.commit()
        self.db.refresh(project)
        return self._project_public(project)

    # ---------- instructor ----------

    def list_cohort_projects(self, user: User, cohort_id: UUID) -> list[InstructorProjectRow]:
        self._require_instructor_access(user, cohort_id)
        projects = list(
            self.db.scalars(
                select(Project)
                .options(selectinload(Project.user), selectinload(Project.reviewer))
                .where(Project.cohort_id == cohort_id)
                .order_by(Project.created_at.desc())
            ).all()
        )
        return [
            InstructorProjectRow(
                project=self._project_public(project),
                user_id=project.user_id,
                email=project.user.email,
                full_name=project.user.full_name,
            )
            for project in projects
        ]

    def review_project(self, user: User, project_id: UUID, payload: ReviewProjectRequest) -> ProjectPublic:
        project = self.db.scalar(
            select(Project).options(selectinload(Project.reviewer)).where(Project.id == project_id)
        )
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        self._require_instructor_access(user, project.cohort_id)
        project.feedback = payload.feedback
        project.status = ProjectStatus(payload.status)
        project.reviewed_by = user.id
        project.reviewed_at = _utcnow()
        self.db.commit()
        self.db.refresh(project)
        NotificationService(self.db).create(
            project.user_id,
            type="project_reviewed",
            title="Project reviewed",
            body=(payload.feedback or "Your project has been reviewed."),
            link="/programmes",
        )
        return self._project_public(project)

    def list_showcase_projects(self) -> list[ShowcaseProject]:
        projects = list(
            self.db.scalars(
                select(Project)
                .options(selectinload(Project.user), selectinload(Project.reviewer))
                .where(Project.is_public.is_(True))
                .order_by(Project.created_at.desc())
            ).all()
        )
        return [
            ShowcaseProject(
                project=self._project_public(project),
                full_name=project.user.full_name,
                country_of_residence=project.user.country_of_residence,
            )
            for project in projects
        ]

        return self._project_public(project)
