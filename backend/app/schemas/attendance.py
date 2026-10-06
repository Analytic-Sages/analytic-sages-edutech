from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AttendanceIntervalPublic(BaseModel):
    joined_at: datetime | None = None
    left_at: datetime | None = None
    duration_seconds: int = 0
    source: str = "summary"


class AttendanceParticipantPublic(BaseModel):
    id: UUID
    provider: str = "realtimekit"
    provider_session_id: str | None = None
    provider_participant_id: str
    custom_participant_id: str | None = None
    display_name: str | None = None
    user_id: UUID | None = None
    user_name: str | None = None
    user_email: str | None = None
    matched: bool = False
    first_joined_at: datetime | None = None
    last_left_at: datetime | None = None
    total_attendance_seconds: int = 0
    status: str | None = None
    sync_status: str = "pending"
    last_synced_at: datetime | None = None
    intervals: list[AttendanceIntervalPublic] = Field(default_factory=list)


class ExpectedStudentRow(BaseModel):
    user_id: UUID
    full_name: str | None = None
    email: str
    has_attendance: bool = False
    status: str | None = None
    total_attendance_seconds: int = 0
    manual_override: bool = False


class SessionAttendanceSyncRow(BaseModel):
    session_id: UUID
    status: str
    provider_session_id: str | None = None
    participants: int = 0
    matched: int = 0
    unmatched: int = 0
    attendance_written: int = 0
    last_synced_at: datetime | None = None
    note: str | None = None


class SessionAttendanceDetail(BaseModel):
    session_id: UUID
    session_title: str
    session_started_at: datetime | None = None
    session_ended_at: datetime | None = None
    sync_status: str = "pending"
    last_synced_at: datetime | None = None
    matched_count: int = 0
    unmatched_count: int = 0
    expected_students: list[ExpectedStudentRow] = Field(default_factory=list)
    participants: list[AttendanceParticipantPublic] = Field(default_factory=list)


class AttendanceSyncResult(BaseModel):
    total: int
    updated: int
    skipped: int
    failed: int
    pending: int = 0
    needs_review: int = 0


class AttendanceResolveRequest(BaseModel):
    user_id: UUID | None = None
    status: str | None = Field(default=None, pattern="^(attended|late|absent|needs_review)$")
    reason: str | None = None