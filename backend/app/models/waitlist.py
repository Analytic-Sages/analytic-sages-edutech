"""Cohort waitlist entries.

When a cohort's registration has closed (or the cohort has started), interested
users join a waitlist instead of being sent to checkout. Each entry is tied to an
existing user profile; the required contact fields (phone / Discord / Telegram)
live on the user, so there is no duplicate form data to keep in sync. This model
is only a record of interest — no approval workflow — so staff can export it.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.classroom import Cohort
    from app.models.user import User


class CohortWaitlistEntry(Base):
    __tablename__ = "cohort_waitlist_entries"
    __table_args__ = (
        UniqueConstraint("cohort_id", "user_id", name="uq_cohort_waitlist_cohort_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cohort_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cohorts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cohort: Mapped[Cohort] = relationship()
    user: Mapped[User] = relationship()