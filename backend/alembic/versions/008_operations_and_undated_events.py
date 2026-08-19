"""Operations role and optional event dates

Revision ID: 008_operations_events
Revises: 007_events
Create Date: 2026-08-19
"""

from typing import Sequence, Union

from alembic import op

revision: str = "008_operations_events"
down_revision: Union[str, None] = "007_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'operations'")
    op.alter_column("events", "starts_at", nullable=True)
    op.alter_column("events", "ends_at", nullable=True)


def downgrade() -> None:
    op.execute("DELETE FROM events WHERE starts_at IS NULL OR ends_at IS NULL")
    op.alter_column("events", "starts_at", nullable=False)
    op.alter_column("events", "ends_at", nullable=False)
