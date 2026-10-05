from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    title: str
    body: str = ""
    link: str | None = None
    is_read: bool = False
    created_at: datetime


class UnreadCount(BaseModel):
    unread: int
