from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.classroom import SessionResource


class AdminCohortOption(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    course_title: str | None = None
    sessions_count: int = 0


class AdminLiveSessionCreate(BaseModel):
    cohort_id: UUID
    title: str = Field(min_length=1, max_length=255)
    week_label: str = Field(default="", max_length=80)
    session_number: int = Field(default=1, ge=1)
    session_type: str = Field(default="teaching", pattern="^(teaching|office_hour)$")
    objectives: list[str] = Field(default_factory=list)
    resources: list[SessionResource] = Field(default_factory=list)
    assignment_summary: str | None = None
    starts_at: datetime
    ends_at: datetime


class AdminLiveSessionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    week_label: str | None = Field(default=None, max_length=80)
    session_number: int | None = Field(default=None, ge=1)
    session_type: str | None = Field(default=None, pattern="^(teaching|office_hour)$")
    objectives: list[str] | None = None
    resources: list[SessionResource] | None = None
    assignment_summary: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: str | None = Field(default=None, pattern="^(scheduled|live|ended|cancelled)$")
    recording_url: str | None = None


class AdminLiveSessionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cohort_id: UUID
    cohort_name: str
    cohort_slug: str
    title: str
    week_label: str
    session_number: int
    session_type: str
    objectives: list[str] = Field(default_factory=list)
    resources: list[SessionResource] = Field(default_factory=list)
    assignment_summary: str | None = None
    starts_at: datetime
    ends_at: datetime
    status: str
    phase: str
    recording_url: str | None = None
    member_count: int = 0
    created_at: datetime
    updated_at: datetime