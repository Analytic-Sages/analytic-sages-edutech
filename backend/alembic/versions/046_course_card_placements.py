"""Add centrally managed course-card placements.

Revision ID: 046_course_card_placements
Revises: 045_sql_excel_cohort_sessions
Create Date: 2026-10-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "046_course_card_placements"
down_revision: Union[str, Sequence[str], None] = "045_sql_excel_cohort_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "course_card_placements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_key", sa.String(length=80), nullable=False),
        sa.Column("section_key", sa.String(length=100), nullable=False, server_default="main"),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("visible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("page_key", "section_key", "course_id", name="uq_course_card_placement_course"),
        sa.UniqueConstraint("page_key", "section_key", "sort_order", name="uq_course_card_placement_order"),
    )
    op.create_index("ix_course_card_placements_page_key", "course_card_placements", ["page_key"])
    op.create_index("ix_course_card_placements_course_id", "course_card_placements", ["course_id"])


def downgrade() -> None:
    op.drop_index("ix_course_card_placements_course_id", table_name="course_card_placements")
    op.drop_index("ix_course_card_placements_page_key", table_name="course_card_placements")
    op.drop_table("course_card_placements")
