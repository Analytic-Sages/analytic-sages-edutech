from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.classroom import SessionResource


class AssignmentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cohort_id: UUID
    session_id: UUID | None = None
    title: str
    description: str = ""
    instructions: str | None = None
    week_label: str = ""
    due_date: datetime | None = None
    max_score: int = 100
    passing_score: int | None = None
    required_fields: list[str] = Field(default_factory=list)
    resources: list[SessionResource] = Field(default_factory=list)
    status: str


class SubmissionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assignment_id: UUID
    user_id: UUID
    status: str
    text_response: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    build_in_public_url: str | None = None
    documentation_url: str | None = None
    files: list[dict[str, Any]] = Field(default_factory=list)
    score: int | None = None
    feedback: str | None = None
    reviewer_name: str | None = None
    reviewed_at: datetime | None = None
    submitted_at: datetime | None = None
    updated_at: datetime


class AssignmentDetailPublic(AssignmentPublic):
    my_submission: SubmissionPublic | None = None


class SubmissionUpsert(BaseModel):
    text_response: str | None = None
    github_url: str | None = Field(default=None, max_length=512)
    live_url: str | None = Field(default=None, max_length=512)
    build_in_public_url: str | None = Field(default=None, max_length=512)
    documentation_url: str | None = Field(default=None, max_length=512)
    files: list[dict[str, Any]] = Field(default_factory=list)
    status: str = Field(default="draft", pattern="^(draft|submitted)$")


class ReviewSubmissionRequest(BaseModel):
    score: int | None = Field(default=None, ge=0)
    feedback: str | None = None
    status: str = Field(pattern="^(submitted|under_review|reviewed|returned)$")


class AssignmentUpsert(BaseModel):
    cohort_id: UUID
    session_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    instructions: str | None = None
    week_label: str = Field(default="", max_length=80)
    due_date: datetime | None = None
    max_score: int = Field(default=100, ge=1)
    passing_score: int | None = Field(default=None, ge=0)
    required_fields: list[str] = Field(default_factory=list)
    resources: list[SessionResource] = Field(default_factory=list)
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")


class InstructorSubmissionRow(BaseModel):
    submission: SubmissionPublic
    user_id: UUID
    email: str
    full_name: str | None = None
    enrollment_status: str = "active"


class AssignmentTrackingPublic(AssignmentPublic):
    student_count: int = 0
    submitted_count: int = 0
    missing_count: int = 0
    reviewed_count: int = 0
    submissions: list[InstructorSubmissionRow] = Field(default_factory=list)
