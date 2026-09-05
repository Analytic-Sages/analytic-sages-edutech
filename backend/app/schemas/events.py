from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.event import EventPlatform, EventType


SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"

PLATFORM_LABELS = {
    EventPlatform.YOUTUBE.value: "YouTube",
    EventPlatform.X_SPACE.value: "X Space",
    EventPlatform.ZOOM.value: "Zoom",
    EventPlatform.OTHER.value: "Live session",
}


def platform_display_name(platform: str | None, platform_label: str | None = None) -> str:
    value = (platform or EventPlatform.YOUTUBE.value).strip().lower()
    if value == EventPlatform.OTHER.value:
        custom = (platform_label or "").strip()
        if custom:
            return custom
    return PLATFORM_LABELS.get(value, PLATFORM_LABELS[EventPlatform.YOUTUBE.value])


class KeepLearningOffer(BaseModel):
    kind: str = Field(pattern=r"^(course|program)$")
    slug: str = Field(min_length=2, max_length=160, pattern=SLUG_PATTERN)


def normalize_keep_learning(value: object) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        return []
    offers: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for raw in value:
        try:
            offer = KeepLearningOffer.model_validate(raw)
        except Exception:
            continue
        key = (offer.kind, offer.slug)
        if key in seen:
            continue
        seen.add(key)
        offers.append({"kind": offer.kind, "slug": offer.slug})
        if len(offers) >= 3:
            break
    return offers


class EventCardPublic(BaseModel):
    id: UUID
    slug: str
    title: str
    event_type: str
    short_description: str
    cover_image: str | None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    timezone: str
    price: int
    currency: str
    is_free: bool
    host_name: str | None
    platform: str = EventPlatform.YOUTUBE.value
    platform_label: str | None = None
    platform_display: str = "YouTube"
    lifecycle: str
    registered: bool = False
    can_register: bool = False
    related_course_slug: str | None = None
    has_recording: bool = False


class EventPublic(EventCardPublic):
    description: str
    learn_topics: list[str] = Field(default_factory=list)
    audience: list[str] = Field(default_factory=list)
    prerequisites: str = ""
    registration_deadline: datetime | None = None
    capacity: int | None = None
    cancelled: bool = False
    can_join: bool = False
    can_watch_recording: bool = False
    youtube_live_url: str | None = None
    recording_url: str | None = None
    keep_learning: list[KeepLearningOffer] = Field(default_factory=list)
    seo_title: str | None = None
    seo_description: str | None = None


class EventRegistrationPublic(BaseModel):
    id: UUID
    status: str
    registered_at: datetime
    join_clicked_at: datetime | None = None
    checked_in_at: datetime | None = None
    event: EventCardPublic


class RegisterRequest(BaseModel):
    source: str | None = Field(default=None, max_length=80)


class RegisterResponse(BaseModel):
    registration_id: UUID
    event_slug: str
    already_registered: bool
    status: str


class JoinResponse(BaseModel):
    youtube_live_url: str
    join_clicked_at: datetime


class CheckInResponse(BaseModel):
    checked_in_at: datetime


class EventWriteBase(BaseModel):
    slug: str = Field(min_length=3, max_length=160, pattern=SLUG_PATTERN)
    title: str = Field(min_length=3, max_length=255)
    event_type: EventType = EventType.WORKSHOP
    short_description: str = Field(default="", max_length=400)
    description: str = Field(default="")
    cover_image: str | None = Field(default=None, max_length=500)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    timezone: str = Field(default="Africa/Lagos", max_length=64)
    price: int = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    registration_deadline: datetime | None = None
    capacity: int | None = Field(default=None, ge=1)
    host_name: str | None = Field(default=None, max_length=255)
    platform: EventPlatform = EventPlatform.YOUTUBE
    platform_label: str | None = Field(default=None, max_length=80)
    youtube_live_url: str | None = Field(default=None, max_length=500)
    recording_url: str | None = Field(default=None, max_length=500)
    learn_topics: list[str] = Field(default_factory=list)
    audience: list[str] = Field(default_factory=list)
    prerequisites: str = ""
    related_course_slug: str | None = Field(default=None, max_length=160)
    keep_learning: list[KeepLearningOffer] = Field(default_factory=list)
    seo_title: str | None = Field(default=None, max_length=255)
    seo_description: str | None = Field(default=None, max_length=400)
    published: bool = False
    cancelled: bool = False

    @field_validator("learn_topics", "audience", mode="before")
    @classmethod
    def _normalize_lists(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    @field_validator("keep_learning", mode="before")
    @classmethod
    def _normalize_keep_learning(cls, value: object) -> list[dict[str, str]]:
        return normalize_keep_learning(value)

    @field_validator(
        "cover_image",
        "youtube_live_url",
        "recording_url",
        "related_course_slug",
        "host_name",
        "platform_label",
    )
    @classmethod
    def _empty_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class EventCreate(EventWriteBase):
    pass


class EventUpdate(BaseModel):
    slug: str | None = Field(default=None, min_length=3, max_length=160, pattern=SLUG_PATTERN)
    title: str | None = Field(default=None, min_length=3, max_length=255)
    event_type: EventType | None = None
    short_description: str | None = Field(default=None, max_length=400)
    description: str | None = None
    cover_image: str | None = Field(default=None, max_length=500)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    timezone: str | None = Field(default=None, max_length=64)
    price: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    registration_deadline: datetime | None = None
    capacity: int | None = Field(default=None, ge=1)
    host_name: str | None = Field(default=None, max_length=255)
    platform: EventPlatform | None = None
    platform_label: str | None = Field(default=None, max_length=80)
    youtube_live_url: str | None = Field(default=None, max_length=500)
    recording_url: str | None = Field(default=None, max_length=500)
    learn_topics: list[str] | None = None
    audience: list[str] | None = None
    prerequisites: str | None = None
    related_course_slug: str | None = Field(default=None, max_length=160)
    keep_learning: list[KeepLearningOffer] | None = None
    seo_title: str | None = Field(default=None, max_length=255)
    seo_description: str | None = Field(default=None, max_length=400)
    published: bool | None = None
    cancelled: bool | None = None

    @field_validator("learn_topics", "audience", mode="before")
    @classmethod
    def _normalize_lists(cls, value: object) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return None

    @field_validator("keep_learning", mode="before")
    @classmethod
    def _normalize_keep_learning(cls, value: object) -> list[dict[str, str]] | None:
        if value is None:
            return None
        return normalize_keep_learning(value)

    @field_validator(
        "cover_image",
        "youtube_live_url",
        "recording_url",
        "related_course_slug",
        "host_name",
        "platform_label",
    )
    @classmethod
    def _empty_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class EventAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: str
    event_type: str
    short_description: str
    description: str
    cover_image: str | None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    timezone: str
    price: int
    currency: str
    registration_deadline: datetime | None
    capacity: int | None
    host_name: str | None
    platform: str = EventPlatform.YOUTUBE.value
    platform_label: str | None = None
    platform_display: str = "YouTube"
    youtube_live_url: str | None
    recording_url: str | None
    learn_topics: list[str] = Field(default_factory=list)
    audience: list[str] = Field(default_factory=list)
    prerequisites: str
    related_course_slug: str | None
    keep_learning: list[KeepLearningOffer] = Field(default_factory=list)
    seo_title: str | None
    seo_description: str | None
    published: bool
    cancelled: bool
    lifecycle: str
    registered_count: int = 0
    created_at: datetime
    updated_at: datetime
