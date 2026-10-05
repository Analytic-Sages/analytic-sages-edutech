from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectPublic(BaseModel):
    id: UUID
    cohort_id: UUID
    user_id: UUID
    title: str
    description: str = ""
    status: str
    github_url: str | None = None
    live_url: str | None = None
    build_in_public_url: str | None = None
    documentation_url: str | None = None
    cover_image: str | None = None
    technologies: list[str] = Field(default_factory=list)
    feedback: str | None = None
    reviewer_name: str | None = None
    reviewed_at: datetime | None = None
    is_public: bool = False
    updated_at: datetime


class ProjectUpsert(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    status: str = Field(default="planned", pattern="^(planned|in_progress|submitted|reviewed|completed)$")
    github_url: str | None = Field(default=None, max_length=512)
    live_url: str | None = Field(default=None, max_length=512)
    build_in_public_url: str | None = Field(default=None, max_length=512)
    documentation_url: str | None = Field(default=None, max_length=512)
    cover_image: str | None = Field(default=None, max_length=512)
    technologies: list[str] = Field(default_factory=list)
    is_public: bool = False


class ReviewProjectRequest(BaseModel):
    feedback: str | None = None
    status: str = Field(pattern="^(submitted|reviewed|completed)$")


class InstructorProjectRow(BaseModel):
    project: ProjectPublic
    user_id: UUID
    email: str
    full_name: str | None = None


class ShowcaseProject(BaseModel):
    project: ProjectPublic
    full_name: str | None = None
    country_of_residence: str | None = None
