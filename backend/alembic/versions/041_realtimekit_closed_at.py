"""Remember when a live meeting was closed on RealtimeKit.

Adds ``live_sessions.realtimekit_closed_at`` so an ended class is kicked and its
recording is stopped once, then left alone on later sweeps.

Revision ID: 041_realtimekit_closed_at
Revises: 040_recording_import
Create Date: 2026-10-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "041_realtimekit_closed_at"
down_revision: Union[str, None] = "040_recording_import"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "live_sessions",
        sa.Column("realtimekit_closed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("live_sessions", "realtimekit_closed_at")
