from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clean_bullets(value: list[str]) -> list[str]:
    cleaned = [item.strip() for item in value if item and item.strip()]
    if len(cleaned) > 5:
        raise ValueError("Use at most 5 bullets")
    return cleaned


def _clean_photo(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    if trimmed.startswith("/") or trimmed.startswith("https://") or trimmed.startswith("http://"):
        return trimmed
    raise ValueError("Photo must be a site path like /instructors/name.jpg or an https URL")


class InstructorPublic(BaseModel):
    id: UUID
    name: str
    title: str = ""
    photo_url: str | None = None
    bullets: list[str] = Field(default_factory=list)
    role_label: str = "Instructor"
    sort_order: int = 0


class InstructorProfileAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    title: str = ""
    photo_url: str | None = None
    bullets: list[str] = Field(default_factory=list)
    course_count: int = 0
    cohort_count: int = 0


class InstructorProfileWrite(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    title: str = Field(default="", max_length=120)
    photo_url: str | None = Field(default=None, max_length=512)
    bullets: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name is required")
        return cleaned

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        return value.strip()

    @field_validator("photo_url")
    @classmethod
    def validate_photo(cls, value: str | None) -> str | None:
        return _clean_photo(value)

    @field_validator("bullets")
    @classmethod
    def validate_bullets(cls, value: list[str]) -> list[str]:
        return _clean_bullets(value)


class InstructorAssignmentItem(BaseModel):
    instructor_id: UUID
    role_label: str = Field(default="Instructor", max_length=80)
    sort_order: int = Field(default=0, ge=0, le=100)

    @field_validator("role_label")
    @classmethod
    def strip_role(cls, value: str) -> str:
        return value.strip() or "Instructor"


class InstructorAssignmentWrite(BaseModel):
    items: list[InstructorAssignmentItem] = Field(default_factory=list)


class AdminCohortInstructorRow(BaseModel):
    id: UUID
    slug: str
    name: str
    status: str
    instructor_count: int
