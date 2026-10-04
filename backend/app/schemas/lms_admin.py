from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AdminCourseUpsert(BaseModel):
    slug: str = Field(min_length=2, max_length=160, pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    long_description: str = ""
    thumbnail: str | None = None
    category: str = "General"
    difficulty: str = "Beginner"
    duration: str = ""
    lessons_count: int = 0
    price: int = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    delivery_type: str = "self_paced"
    is_free: bool = False
    certificate_enabled: bool = False
    published: bool = False


class AdminCourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    long_description: str | None = None
    thumbnail: str | None = None
    category: str | None = None
    difficulty: str | None = None
    duration: str | None = None
    price: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    delivery_type: str | None = None
    is_free: bool | None = None
    certificate_enabled: bool | None = None
    published: bool | None = None


class AdminModuleUpsert(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    order_index: int | None = Field(default=None, ge=1)


class AdminModuleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    order_index: int | None = Field(default=None, ge=1)


class AdminLessonUpsert(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(
        default=None, max_length=180, pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    subtitle: str | None = None
    description: str = ""
    video_provider: str = "youtube"  # youtube | cloudflare_stream
    video_id: str | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    order_index: int | None = Field(default=None, ge=1)
    published: bool = True
    what_you_learn: list[str] = Field(default_factory=list)
    key_concepts: list[str] = Field(default_factory=list)


class AdminLessonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    subtitle: str | None = None
    description: str | None = None
    video_provider: str | None = None
    video_id: str | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    order_index: int | None = Field(default=None, ge=1)
    published: bool | None = None
    what_you_learn: list[str] | None = None
    key_concepts: list[str] | None = None


class AdminLessonResourceUpsert(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=1, max_length=1000)
    kind: str = Field(default="other", pattern="^(pdf|slides|dataset|code|repo|reading|doc|other)$")


class AdminLessonRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module_id: UUID
    slug: str
    title: str
    subtitle: str | None
    description: str
    video_provider: str
    video_id: str | None
    duration_seconds: int | None
    order_index: int
    published: bool
    what_you_learn: list[str] = Field(default_factory=list)
    key_concepts: list[str] = Field(default_factory=list)
    resources: list[dict] = Field(default_factory=list)


class AdminModuleRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    order_index: int
    lessons: list[AdminLessonRow] = Field(default_factory=list)


class AdminCourseDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: str
    description: str
    long_description: str
    thumbnail: str | None
    category: str
    difficulty: str
    duration: str
    lessons_count: int
    price: int
    currency: str
    delivery_type: str
    is_free: bool
    certificate_enabled: bool
    published: bool
    modules: list[AdminModuleRow] = Field(default_factory=list)


class AdminVideoUploadResponse(BaseModel):
    uid: str
    upload_url: str
    embed_url: str | None = None
    hls_url: str | None = None
    thumbnail_url: str | None = None
    mode: str  # live | mock


class AdminVideoInfo(BaseModel):
    uid: str
    status: str
    duration_seconds: int | None = None
    thumbnail_url: str | None = None
    embed_url: str | None = None
    hls_url: str | None = None
    mode: str