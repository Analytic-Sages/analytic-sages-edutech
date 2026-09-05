"""Add keep_learning preferred offers on events.

Revision ID: 025_event_keep_learning
Revises: 024_event_platform_x_space
Create Date: 2026-09-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "025_event_keep_learning"
down_revision: Union[str, None] = "024_event_platform_x_space"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column(
            "keep_learning",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    # Seed from legacy related_course_slug when present.
    op.execute(
        """
        UPDATE events
        SET keep_learning = jsonb_build_array(
          jsonb_build_object('kind', 'course', 'slug', related_course_slug)
        )
        WHERE related_course_slug IS NOT NULL
          AND btrim(related_course_slug) <> ''
          AND (keep_learning IS NULL OR keep_learning = '[]'::jsonb)
        """
    )


def downgrade() -> None:
    op.drop_column("events", "keep_learning")
