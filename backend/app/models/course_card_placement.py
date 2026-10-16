from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CourseCardPlacement(Base):
    """A course's position and visibility within a named page/section placement."""

    __tablename__ = "course_card_placements"
    __table_args__ = (
        UniqueConstraint("page_key", "section_key", "course_id", name="uq_course_card_placement_course"),
        UniqueConstraint("page_key", "section_key", "sort_order", name="uq_course_card_placement_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    section_key: Mapped[str] = mapped_column(String(100), nullable=False, default="main")
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    course = relationship("Course")
