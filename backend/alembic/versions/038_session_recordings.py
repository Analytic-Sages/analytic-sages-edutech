"""Persistent session recordings.

Revision ID: 038_session_recordings
Revises: 037_cohort_waitlist
Create Date: 2026-10-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "038_session_recordings"
down_revision: Union[str, None] = "037_cohort_waitlist"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE recording_status AS ENUM ('processing', 'ready', 'failed')")
    recording_status = postgresql.ENUM(
        "processing", "ready", "failed", name="recording_status", create_type=False
    )

    op.create_table(
        "session_recordings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="cloudflare_stream"),
        sa.Column("provider_recording_id", sa.String(length=120), nullable=True),
        sa.Column("status", recording_status, nullable=False, server_default="processing"),
        sa.Column(
            "storage_provider", sa.String(length=40), nullable=False, server_default="cloudflare_stream"
        ),
        sa.Column("storage_key", sa.String(length=255), nullable=True),
        sa.Column("recording_url", sa.String(length=512), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["session_id"], ["live_sessions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("session_id", name="uq_session_recordings_session"),
    )
    op.create_index("ix_session_recordings_session_id", "session_recordings", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_session_recordings_session_id", table_name="session_recordings")
    op.drop_table("session_recordings")
    op.execute("DROP TYPE recording_status")