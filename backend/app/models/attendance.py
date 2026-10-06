from __future__ import annotations

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

from app.core.live import AttendanceStatus, AttendanceSyncStatus
from app.db.enums import pg_enum
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.classroom import LiveSession
    from app.models.user import User


class Attendance(Base):
    """One authoritative attendance record per (session, student).

    Rows are written either by hand (instructor marking) or imported from a
    provider (RealtimeKit) via ``AttendanceSyncService``. Provider-imported rows
    carry identity/session/interval metadata used to reconcile them; a manual
    override always wins and is never clobbered by a later sync.
    """

    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("session_id", "user_id", name="uq_attendance_session_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("live_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[AttendanceStatus] = mapped_column(
        pg_enum(AttendanceStatus, name="attendance_status"),
        nullable=False,
        default=AttendanceStatus.ATTENDED,
    )
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ---- provider reconciliation metadata (nullable: manual rows may not have it) ----
    provider: Mapped[str | None] = mapped_column(String(40), nullable=True)
    provider_meeting_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    provider_session_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    provider_participant_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    first_joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_attendance_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sync_status: Mapped[AttendanceSyncStatus | None] = mapped_column(
        pg_enum(AttendanceSyncStatus, name="attendance_sync_status"), nullable=True
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # A human corrected this row; subsequent provider syncs must leave it alone.
    manual_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    overridden_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    session: Mapped[LiveSession] = relationship()
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    recorder: Mapped[User | None] = relationship(foreign_keys=[recorded_by])
    overrider: Mapped[User | None] = relationship(foreign_keys=[overridden_by])


class AttendanceParticipant(Base):
    """A raw participant session imported from the provider (RealtimeKit).

    Kept even when it cannot be matched to an enrolled student so nothing is lost
    and an instructor can resolve it. ``user_id`` is only set when the participant
    is confidently matched (via the authenticated ``custom_participant_id``), never
    by guessing a display name.
    """

    __tablename__ = "attendance_participants"
    __table_args__ = (
        UniqueConstraint(
            "session_id", "provider_participant_id", name="uq_attendance_participants_session_provider"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("live_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="realtimekit")
    provider_session_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    provider_participant_id: Mapped[str] = mapped_column(String(120), nullable=False)
    # Identity RealtimeKit echoes back: the LMS user id we passed on join.
    custom_participant_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Matched LMS user (null = unmatched → needs instructor review).
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    first_joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_attendance_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[AttendanceStatus | None] = mapped_column(
        pg_enum(AttendanceStatus, name="attendance_status"), nullable=True
    )
    sync_status: Mapped[AttendanceSyncStatus] = mapped_column(
        pg_enum(AttendanceSyncStatus, name="attendance_sync_status"),
        nullable=False,
        default=AttendanceSyncStatus.PENDING,
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Raw provider payload — preserved for troubleshooting.
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    session: Mapped[LiveSession] = relationship()
    user: Mapped[User | None] = relationship(foreign_keys=[user_id])
    intervals: Mapped[list[AttendanceInterval]] = relationship(
        back_populates="participant",
        cascade="all, delete-orphan",
        order_by="AttendanceInterval.joined_at",
    )


class AttendanceInterval(Base):
    """A single contiguous presence window within a participant's session.

    Reconnects and correction passes create multiple rows, so total attendance can
    be computed from non-overlapping intervals and audited precisely.
    """

    __tablename__ = "attendance_intervals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attendance_participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Provider event id when the interval came from a discrete peer event.
    provider_event_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Where the interval came from: "peer_events" or "summary".
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="summary")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    participant: Mapped[AttendanceParticipant] = relationship(back_populates="intervals")
