from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.instructors import InstructorPublic


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
    session_type: Literal["teaching", "office_hour"] = "teaching"
    objectives: list[str] = Field(default_factory=list)
    resources: list[SessionResource] = Field(default_factory=list)
    assignment_summary: str | None = None
    description: str | None = None
    timezone: str = "UTC"
    meeting_url: str | None = None
    instructor_name: str | None = None
    starts_at: datetime
    ends_at: datetime
    status: Literal["scheduled", "live", "ended", "cancelled"]
    phase: Literal["upcoming", "live", "ended", "cancelled"]
    recording_url: str | None = None
    # Permanent recording state + access-gated playback path (see /cohorts/.../recording).
    recording_status: Literal["none", "processing", "ready", "failed"] = "none"
    recording_watch_url: str | None = None
    can_join: bool = False
    member_role: Literal["student", "instructor", "ta"] | None = None
    access_blocked: bool = False
    access_blocked_reason: str | None = None


class ClassroomJoinResponse(BaseModel):
    session_id: UUID
    mode: Literal["live", "mock"]
    auth_token: str | None = None
    meeting_id: str | None = None
    preset: str
    display_name: str
    phase: Literal["upcoming", "live", "ended", "cancelled"]
    message: str | None = None


class ClassroomCalendarFeed(BaseModel):
    """Personal subscribe URL for classroom sessions (used by calendar apps)."""

    token: str
    url: str
    webcal_url: str


class SessionRecordingPlayback(BaseModel):
    """Access-gated playback for a concluded session's permanent recording."""

    session_id: UUID
    status: Literal["none", "processing", "ready", "failed"] = "none"
    watch_url: str | None = None
    duration_seconds: int | None = None
    embed_url: str | None = None
    hls_url: str | None = None


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
    instructors: list[InstructorPublic] = Field(default_factory=list)
    # When true, registration is closed and the CTA links to the waitlist.
    waitlist_open: bool = False
