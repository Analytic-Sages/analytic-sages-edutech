"""RealtimeKit attendance reconciliation.

Adds provider metadata to ``attendance`` (join/leave, intervals total, sync state,
manual-override provenance), a ``needs_review`` attendance status, and two new
tables: ``attendance_participants`` (raw provider participants, incl. unmatched)
and ``attendance_intervals`` (discrete presence windows for reconnects/audit).

Revision ID: 039_realtimekit_attendance
Revises: 038_session_recordings
Create Date: 2026-10-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "039_realtimekit_attendance"
down_revision: Union[str, None] = "038_session_recordings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # New status value for imported-but-unmatched attendance. ADD VALUE must run
    # outside the migration transaction on some Postgres versions.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE attendance_status ADD VALUE IF NOT EXISTS 'needs_review'")

    op.execute(
        "CREATE TYPE attendance_sync_status AS ENUM ('ok', 'pending', 'needs_review', 'error')"
    )
    attendance_sync_status = postgresql.ENUM(
        "ok", "pending", "needs_review", "error", name="attendance_sync_status", create_type=False
    )

    # ---- provider metadata on the authoritative attendance row ----
    op.add_column("attendance", sa.Column("provider", sa.String(length=40), nullable=True))
    op.add_column("attendance", sa.Column("provider_meeting_id", sa.String(length=120), nullable=True))
    op.add_column("attendance", sa.Column("provider_session_id", sa.String(length=120), nullable=True))
    op.add_column("attendance", sa.Column("provider_participant_id", sa.String(length=120), nullable=True))
    op.add_column("attendance", sa.Column("first_joined_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("attendance", sa.Column("last_left_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "attendance",
        sa.Column("total_attendance_seconds", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("attendance", sa.Column("sync_status", attendance_sync_status, nullable=True))
    op.add_column("attendance", sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "attendance",
        sa.Column("manual_override", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("attendance", sa.Column("override_reason", sa.Text(), nullable=True))
    op.add_column("attendance", sa.Column("overridden_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_attendance_overridden_by_users", "attendance", "users", ["overridden_by"], ["id"],
        ondelete="SET NULL",
    )

    # ---- raw provider participants (kept even when unmatched) ----
    op.create_table(
        "attendance_participants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="realtimekit"),
        sa.Column("provider_session_id", sa.String(length=120), nullable=True),
        sa.Column("provider_participant_id", sa.String(length=120), nullable=False),
        sa.Column("custom_participant_id", sa.String(length=120), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("first_joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_attendance_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            postgresql.ENUM(
                "attended", "late", "absent", "needs_review",
                name="attendance_status", create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("sync_status", attendance_sync_status, nullable=False, server_default="pending"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["live_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "session_id", "provider_participant_id", name="uq_attendance_participants_session_provider"
        ),
    )
    op.create_index("ix_attendance_participants_session_id", "attendance_participants", ["session_id"])
    op.create_index("ix_attendance_participants_user_id", "attendance_participants", ["user_id"])
    op.create_index(
        "ix_attendance_participants_custom_participant_id", "attendance_participants", ["custom_participant_id"]
    )

    # ---- discrete presence windows (reconnects + audit) ----
    op.create_table(
        "attendance_intervals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("participant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_event_id", sa.String(length=120), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=False, server_default="summary"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["participant_id"], ["attendance_participants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_attendance_intervals_participant_id", "attendance_intervals", ["participant_id"])


def downgrade() -> None:
    op.drop_index("ix_attendance_intervals_participant_id", table_name="attendance_intervals")
    op.drop_table("attendance_intervals")

    op.drop_index("ix_attendance_participants_custom_participant_id", table_name="attendance_participants")
    op.drop_index("ix_attendance_participants_user_id", table_name="attendance_participants")
    op.drop_index("ix_attendance_participants_session_id", table_name="attendance_participants")
    op.drop_table("attendance_participants")

    op.drop_constraint("fk_attendance_overridden_by_users", "attendance", type_="foreignkey")
    op.drop_column("attendance", "overridden_by")
    op.drop_column("attendance", "override_reason")
    op.drop_column("attendance", "manual_override")
    op.drop_column("attendance", "last_synced_at")
    op.drop_column("attendance", "sync_status")
    op.drop_column("attendance", "total_attendance_seconds")
    op.drop_column("attendance", "last_left_at")
    op.drop_column("attendance", "first_joined_at")
    op.drop_column("attendance", "provider_participant_id")
    op.drop_column("attendance", "provider_session_id")
    op.drop_column("attendance", "provider_meeting_id")
    op.drop_column("attendance", "provider")

    op.execute("DROP TYPE attendance_sync_status")
    # Postgres cannot remove a single enum value; leaving 'needs_review' is harmless.