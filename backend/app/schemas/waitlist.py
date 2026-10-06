from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# Contact fields that must be present on the user's profile before joining.
REQUIRED_WAITLIST_FIELDS = ("phone_number", "discord_username", "telegram_username")


class WaitlistJoinRequest(BaseModel):
    note: str | None = Field(default=None, max_length=1000)


class WaitlistEntryPublic(BaseModel):
    id: UUID
    cohort_id: UUID
    created_at: datetime


class WaitlistStatusPublic(BaseModel):
    """Whether the current user is on the waitlist and what's still missing."""

    is_open: bool = False
    is_on_waitlist: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    entry: WaitlistEntryPublic | None = None


class AdminWaitlistRow(BaseModel):
    user_id: UUID
    full_name: str | None = None
    email: str
    phone_number: str | None = None
    phone_country_code: str | None = None
    country_of_residence: str | None = None
    discord_username: str | None = None
    telegram_username: str | None = None
    note: str | None = None
    created_at: datetime


class AdminWaitlistResponse(BaseModel):
    cohort_id: UUID
    cohort_slug: str
    cohort_name: str
    is_open: bool = False
    count: int = 0
    entries: list[AdminWaitlistRow] = Field(default_factory=list)