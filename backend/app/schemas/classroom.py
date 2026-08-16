from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SessionResource(BaseModel):
    title: str
    url: str
    kind: Literal["slides", "dataset", "repo", "reading", "doc", "other"] = "other"


class LiveSessionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cohort_id: UUID
    cohort_name: str
    cohort_slug: str
    course_title: str | None = None
    title: str
    week_label: str
    session_number: int
    objectives: list[str] = Field(default_factory=list)
    resources: list[SessionResource] = Field(default_factory=list)
    assignment_summary: str | None = None
    starts_at: datetime
    ends_at: datetime
    status: Literal["scheduled", "live", "ended", "cancelled"]
    phase: Literal["upcoming", "live", "ended", "cancelled"]
    recording_url: str | None = None
    can_join: bool = False
    member_role: Literal["student", "instructor", "ta"] | None = None


class ClassroomJoinResponse(BaseModel):
    session_id: UUID
    mode: Literal["live", "mock"]
    auth_token: str | None = None
    meeting_id: str | None = None
    preset: str
    display_name: str
    phase: Literal["upcoming", "live", "ended", "cancelled"]
    message: str | None = None


class PublicCohortCard(BaseModel):
    """Marketing-safe cohort summary for Instructor-Led pages (no join tokens)."""

    id: UUID
    name: str
    slug: str
    description: str
    status: Literal["draft", "open", "active", "completed"]
    registration_deadline: datetime | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    price: int = 0
    currency: str = "USD"
    course_title: str | None = None
    course_slug: str | None = None
    next_session_title: str | None = None
    next_session_starts_at: datetime | None = None
    next_session_phase: Literal["upcoming", "live", "ended", "cancelled"] | None = None
    sessions_count: int = 0
