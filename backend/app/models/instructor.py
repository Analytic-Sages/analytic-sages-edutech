from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.classroom import Cohort
    from app.models.course import Course


class InstructorProfile(Base):
    """Public-facing instructor bio. Independent of classroom login accounts."""

    __tablename__ = "instructor_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bullets: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
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

    course_links: Mapped[list[CourseInstructor]] = relationship(
        back_populates="instructor", cascade="all, delete-orphan"
    )
    cohort_links: Mapped[list[CohortInstructor]] = relationship(
        back_populates="instructor", cascade="all, delete-orphan"
    )


class CourseInstructor(Base):
    __tablename__ = "course_instructors"
    __table_args__ = (
        UniqueConstraint("course_id", "instructor_id", name="uq_course_instructors_course_instructor"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    instructor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instructor_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_label: Mapped[str] = mapped_column(String(80), nullable=False, default="Instructor")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    course: Mapped[Course] = relationship(back_populates="instructor_links")
    instructor: Mapped[InstructorProfile] = relationship(back_populates="course_links")


class CohortInstructor(Base):
    __tablename__ = "cohort_instructors"
    __table_args__ = (
        UniqueConstraint("cohort_id", "instructor_id", name="uq_cohort_instructors_cohort_instructor"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cohort_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    instructor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instructor_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_label: Mapped[str] = mapped_column(String(80), nullable=False, default="Instructor")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    cohort: Mapped[Cohort] = relationship(back_populates="instructor_links")
    instructor: Mapped[InstructorProfile] = relationship(back_populates="cohort_links")
