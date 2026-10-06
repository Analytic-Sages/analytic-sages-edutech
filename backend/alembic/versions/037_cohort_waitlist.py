"""Cohort waitlist entries.

Revision ID: 037_cohort_waitlist
Revises: 036_notifications_portfolio
Create Date: 2026-10-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "037_cohort_waitlist"
down_revision: Union[str, None] = "036_notifications_portfolio"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cohort_waitlist_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["cohort_id"], ["cohorts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("cohort_id", "user_id", name="uq_cohort_waitlist_cohort_user"),
    )
    op.create_index("ix_cohort_waitlist_entries_cohort_id", "cohort_waitlist_entries", ["cohort_id"])
    op.create_index("ix_cohort_waitlist_entries_user_id", "cohort_waitlist_entries", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_cohort_waitlist_entries_user_id", table_name="cohort_waitlist_entries")
    op.drop_index("ix_cohort_waitlist_entries_cohort_id", table_name="cohort_waitlist_entries")
    op.drop_table("cohort_waitlist_entries")