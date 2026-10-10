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
    description: str | None = None
    timezone: str = Field(default="UTC", max_length=64)
    meeting_url: str | None = Field(default=None, max_length=512)
    instructor_user_id: UUID | None = None
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
    description: str | None = None
    timezone: str | None = Field(default=None, max_length=64)
    meeting_url: str | None = Field(default=None, max_length=512)
    instructor_user_id: UUID | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: str | None = Field(default=None, pattern="^(scheduled|live|ended|cancelled)$")
    recording_url: str | None = None


class AdminRecordingSyncResult(BaseModel):
    """Summary of a bulk recording sync across a cohort (or all cohorts)."""

    total: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0


class RecordingCandidateSession(BaseModel):
    """A historical LMS session that may match an existing RealtimeKit recording."""

    session_id: UUID
    cohort_id: UUID
    cohort_name: str
    title: str
    week_label: str = ""
    starts_at: datetime
    match: str  # "meeting" | "title" | "date"
    has_recording: bool = False


class RecordingImportPreview(BaseModel):
    """Verified metadata for an existing RealtimeKit recording + candidate sessions.

    Returned before any change so an admin can confirm the correct session instead
    of the platform guessing.
    """

    recording_id: str
    title: str | None = None
    status: str | None = None
    started_at: datetime | None = None
    duration_seconds: int | None = None
    meeting_id: str | None = None
    provider_session_id: str | None = None
    has_download_url: bool = False
    download_url_expires_at: datetime | None = None
    already_linked_session_id: UUID | None = None
    candidates: list[RecordingCandidateSession] = Field(default_factory=list)
    ambiguous: bool = False
    note: str | None = None


class RecordingArchiveResult(BaseModel):
    """Outcome of copying one RealtimeKit recording into the private R2 bucket."""

    recording_id: str
    success: bool
    outcome: str
    detail: str
    bucket: str | None = None
    object_key: str | None = None
    size_bytes: int | None = None
    provider_status: str | None = None


class RecordingImportRequest(BaseModel):
    """Attach an existing RealtimeKit recording to a specific LMS session.

    ``download_url`` is an optional manual fallback for recovery when the recording
    API cannot be reached; it is fetched-copied immediately and never persisted.
    """

    recording_id: str = Field(min_length=3, max_length=120)
    download_url: str | None = Field(default=None, max_length=2048)
    reason: str | None = Field(default=None, max_length=500)
    # Explicit instructor confirmation; the previous provider asset is not deleted.
    replace_existing: bool = False


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
    description: str | None = None
    timezone: str = "UTC"
    meeting_url: str | None = None
    instructor_name: str | None = None
    starts_at: datetime
    ends_at: datetime
    status: str
    phase: str
    recording_url: str | None = None
    recording_status: str = "none"
    member_count: int = 0
    created_at: datetime
    updated_at: datetime