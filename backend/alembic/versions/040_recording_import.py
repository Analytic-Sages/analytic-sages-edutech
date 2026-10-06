"""Link existing RealtimeKit recordings to historical sessions.

Adds ``session_recordings.realtimekit_recording_id`` (RealtimeKit's own recording
id — distinct from the meeting id) with a unique constraint so a historical
recording can be traced and never double-linked to two LMS sessions.

Revision ID: 040_recording_import
Revises: 039_realtimekit_attendance
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "040_recording_import"
down_revision: Union[str, None] = "039_realtimekit_attendance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "session_recordings",
        sa.Column("realtimekit_recording_id", sa.String(length=120), nullable=True),
    )
    # Postgres treats NULLs as distinct, so existing rows are unaffected.
    op.create_unique_constraint(
        "uq_session_recordings_realtimekit_recording",
        "session_recordings",
        ["realtimekit_recording_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_session_recordings_realtimekit_recording", "session_recordings", type_="unique"
    )
    op.drop_column("session_recordings", "realtimekit_recording_id")