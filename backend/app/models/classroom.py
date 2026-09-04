from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.enums import pg_enum
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.instructor import CohortInstructor
    from app.models.user import User


class CohortStatus(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    ACTIVE = "active"
    COMPLETED = "completed"


class CohortMemberRole(str, enum.Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    TA = "ta"


class LiveSessionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    ENDED = "ended"
    CANCELLED = "cancelled"


class Cohort(Base):
    __tablename__ = "cohorts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[CohortStatus] = mapped_column(
        pg_enum(CohortStatus, name="cohort_status"),
        nullable=False,
        default=CohortStatus.DRAFT,
    )
    registration_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    referral_commission_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
    instructor_links: Mapped[list[CohortInstructor]] = relationship(
        back_populates="cohort",
        cascade="all, delete-orphan",
        order_by="CohortInstructor.sort_order",
    )
    members: Mapped[list[CohortMember]] = relationship(
        back_populates="cohort", cascade="all, delete-orphan"
    )
    sessions: Mapped[list[LiveSession]] = relationship(
        back_populates="cohort", cascade="all, delete-orphan"
    )


class CohortMember(Base):
    __tablename__ = "cohort_members"
    __table_args__ = (
        UniqueConstraint("cohort_id", "user_id", name="uq_cohort_members_cohort_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cohort_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[CohortMemberRole] = mapped_column(
        pg_enum(CohortMemberRole, name="cohort_member_role"),
        nullable=False,
        default=CohortMemberRole.STUDENT,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cohort: Mapped[Cohort] = relationship(back_populates="members")
    user: Mapped[User] = relationship()


class LiveSession(Base):
    __tablename__ = "live_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cohort_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    week_label: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    session_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    objectives: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    resources: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    assignment_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[LiveSessionStatus] = mapped_column(
        pg_enum(LiveSessionStatus, name="live_session_status"),
        nullable=False,
        default=LiveSessionStatus.SCHEDULED,
    )
    realtimekit_meeting_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    recording_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    cohort: Mapped[Cohort] = relationship(back_populates="sessions")
