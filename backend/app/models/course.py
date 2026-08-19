from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.enrollment import Enrollment
    from app.models.lms import CourseModule
    from app.models.payment import Payment


class Course(Base):
    """Catalog course. Self-paced curriculum lives in modules/lessons."""

    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    long_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    thumbnail: Mapped[str | None] = mapped_column(String(512), nullable=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, default="General")
    difficulty: Mapped[str] = mapped_column(String(40), nullable=False, default="Beginner")
    duration: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lessons_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="NGN")
    delivery_type: Mapped[str] = mapped_column(String(32), nullable=False, default="self_paced")
    is_free: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    certificate_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    enrollments: Mapped[list[Enrollment]] = relationship(back_populates="course")
    payments: Mapped[list[Payment]] = relationship(back_populates="course")
    modules: Mapped[list[CourseModule]] = relationship(
        "CourseModule",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="CourseModule.order_index",
    )
