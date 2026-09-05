"""Add event platform fields and x_space event type.

Revision ID: 024_event_platform_x_space
Revises: 023_opp_logo_compensation
Create Date: 2026-09-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "024_event_platform_x_space"
down_revision: Union[str, None] = "023_opp_logo_compensation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'x_space'")
    op.add_column(
        "events",
        sa.Column("platform", sa.String(length=40), nullable=False, server_default="youtube"),
    )
    op.add_column(
        "events",
        sa.Column("platform_label", sa.String(length=80), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("events", "platform_label")
    op.drop_column("events", "platform")
    # Postgres cannot easily remove enum values
