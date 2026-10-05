from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.classroom import LiveSessionPublic


class ProgrammePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: str
    description: str = ""
    overview: str = ""
    learning_outcomes: list[str] = Field(default_factory=list)
    duration: str = ""
    programme_type: str = "live"
    status: str
    cover_image: str | None = None
    requirements: list[str] = Field(default_factory=list)
    certificate_requirements: dict[str, Any] = Field(default_factory=dict)
    course_id: UUID | None = None


class ProgrammeCohortPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    status: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    timezone: str = "UTC"
    capacity: int | None = None
    price: int = 0
    currency: str = "USD"
    community_links: dict[str, Any] = Field(default_factory=dict)


class ProgrammeDetailPublic(ProgrammePublic):
    cohorts: list[ProgrammeCohortPublic] = Field(default_factory=list)


class AttendanceSummaryPublic(BaseModel):
    attended: int = 0
    late: int = 0
    absent: int = 0
    total: int = 0


class AttendanceRecordPublic(BaseModel):
    session_id: UUID
    session_title: str
    starts_at: datetime
    status: str
    recorded_at: datetime
    note: str | None = None


class MyLiveEnrollmentPublic(BaseModel):
    programme_id: UUID | None = None
    programme_slug: str | None = None
    programme_title: str | None = None
    cohort_id: UUID
    cohort_name: str
    cohort_slug: str
    enrollment_status: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    timezone: str = "UTC"
    progress_percent: int = 0
    attendance_attended: int = 0
    attendance_total: int = 0
    next_session: LiveSessionPublic | None = None


class CohortStudentDetailPublic(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str = ""
    status: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    timezone: str = "UTC"
    capacity: int | None = None
    community_links: dict[str, Any] = Field(default_factory=dict)
    programme: ProgrammePublic | None = None
    progress_percent: int = 0
    attendance: AttendanceSummaryPublic = Field(default_factory=AttendanceSummaryPublic)
    sessions: list[LiveSessionPublic] = Field(default_factory=list)


class AttendanceWriteItem(BaseModel):
    user_id: UUID
    session_id: UUID
    status: str = Field(pattern="^(attended|late|absent)$")
    note: str | None = None


class AttendanceBulkWrite(BaseModel):
    items: list[AttendanceWriteItem] = Field(default_factory=list)


class InstructorStudentRow(BaseModel):
    user_id: UUID
    email: str
    full_name: str | None = None
    country_of_residence: str | None = None
    enrollment_status: str
    attendance_attended: int = 0
    attendance_total: int = 0
    progress_percent: int = 0


class ProgrammeUpsert(BaseModel):
    slug: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    overview: str = ""
    learning_outcomes: list[str] = Field(default_factory=list)
    duration: str = ""
    programme_type: str = "live"
    status: str = Field(default="draft", pattern="^(draft|upcoming|active|completed|archived)$")
    cover_image: str | None = None
    requirements: list[str] = Field(default_factory=list)
    certificate_requirements: dict[str, Any] = Field(default_factory=dict)
    course_id: UUID | None = None


class CohortAdminUpsert(BaseModel):
    programme_id: UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=160)
    description: str = ""
    status: str = Field(default="draft", pattern="^(draft|open|active|completed)$")
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    registration_deadline: datetime | None = None
    timezone: str = Field(default="UTC", max_length=64)
    capacity: int | None = Field(default=None, ge=1)
    price: int = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    community_links: dict[str, Any] = Field(default_factory=dict)
