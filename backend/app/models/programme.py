from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.live import ProgrammeStatus
from app.db.enums import pg_enum
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.classroom import Cohort
    from app.models.course import Course


class Programme(Base):
    """Reusable live learning offering. A Cohort is a specific delivery of a Programme."""

    __tablename__ = "programmes"
    __table_args__ = (UniqueConstraint("slug", name="uq_programmes_slug"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    overview: Mapped[str] = mapped_column(Text, nullable=False, default="")
    learning_outcomes: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    duration: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    programme_type: Mapped[str] = mapped_column(String(40), nullable=False, default="live")
    status: Mapped[ProgrammeStatus] = mapped_column(
        pg_enum(ProgrammeStatus, name="programme_status"),
        nullable=False,
        default=ProgrammeStatus.DRAFT,
    )
    cover_image: Mapped[str | None] = mapped_column(String(512), nullable=True)
    requirements: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    certificate_requirements: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    course: Mapped[Course | None] = relationship()
    cohorts: Mapped[list[Cohort]] = relationship(back_populates="programme")
