from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LessonResourcePublic(BaseModel):
    label: str
    url: str


class LessonOutlinePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: str
    subtitle: str | None = None
    duration_seconds: int | None = None
    order_index: int
    video_provider: str
    video_id: str | None = None
    completed: bool = False


class ModuleOutlinePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    order_index: int
    lessons: list[LessonOutlinePublic]


class SelfPacedCourseCard(BaseModel):
    id: UUID
    slug: str
    title: str
    description: str
    thumbnail: str | None
    category: str
    difficulty: str
    duration: str
    estimated_minutes: int
    lessons_count: int
    price: int
    currency: str
    is_free: bool
    delivery_type: str
    certificate_enabled: bool


class SelfPacedCoursePublic(SelfPacedCourseCard):
    long_description: str
    published: bool
    enrolled: bool = False
    completed: bool = False
    progress_percent: int = 0
    lessons_completed: int = 0
    resume_lesson_slug: str | None = None
    modules: list[ModuleOutlinePublic] = Field(default_factory=list)


class LessonDetailPublic(BaseModel):
    id: UUID
    slug: str
    title: str
    subtitle: str | None = None
    description: str
    module_id: UUID
    module_title: str
    lesson_number: int
    lessons_total: int
    duration_seconds: int | None = None
    video_provider: str
    video_id: str | None = None
    what_you_learn: list[str] = Field(default_factory=list)
    key_concepts: list[str] = Field(default_factory=list)
    resources: list[LessonResourcePublic] = Field(default_factory=list)
    completed: bool = False
    prev_slug: str | None = None
    next_slug: str | None = None
    course_title: str
    course_slug: str
    course_completed: bool = False
    progress_percent: int = 0
    lessons_completed: int = 0


class CourseProgressPublic(BaseModel):
    course_id: UUID
    course_slug: str
    enrollment_id: UUID
    status: str
    enrolled_at: datetime
    completed_at: datetime | None
    last_activity_at: datetime | None
    progress_percent: int
    lessons_completed: int
    lessons_total: int
    resume_lesson_slug: str | None = None
    completed_lesson_slugs: list[str] = Field(default_factory=list)


class EnrollmentWithProgress(BaseModel):
    id: UUID
    course_id: UUID
    status: str
    enrolled_at: datetime
    completed_at: datetime | None
    last_activity_at: datetime | None
    progress_percent: int
    lessons_completed: int
    lessons_total: int
    resume_lesson_slug: str | None = None
    course: SelfPacedCourseCard


class EnrollResponse(BaseModel):
    enrollment_id: UUID
    course_slug: str
    already_enrolled: bool
    resume_lesson_slug: str | None = None
    status: str


class LessonCompleteResponse(BaseModel):
    lesson_slug: str
    completed: bool
    course_completed: bool
    progress_percent: int
    lessons_completed: int
    lessons_total: int
    next_slug: str | None = None


class AdminCourseRow(BaseModel):
    id: UUID
    slug: str
    title: str
    published: bool
    is_free: bool
    delivery_type: str
    price: int
    currency: str
    lessons_count: int
    modules_count: int
    enrollments_count: int
    completions_count: int
    avg_progress_percent: int
    last_activity_at: datetime | None = None


class AdminCourseAnalytics(BaseModel):
    course: AdminCourseRow
    enrollments_count: int
    active_learners: int
    lessons_completed: int
    completion_rate: float
    avg_progress_percent: int
    last_activity_at: datetime | None = None
