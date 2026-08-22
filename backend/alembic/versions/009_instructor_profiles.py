"""Instructor profiles for public course and cohort pages

Revision ID: 009_instructor_profiles
Revises: 008_operations_events
Create Date: 2026-08-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009_instructor_profiles"
down_revision: Union[str, None] = "008_operations_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "instructor_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("photo_url", sa.String(length=512), nullable=True),
        sa.Column(
            "bullets",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "course_instructors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instructor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_label", sa.String(length=80), nullable=False, server_default="Instructor"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["instructor_id"], ["instructor_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "instructor_id", name="uq_course_instructors_course_instructor"),
    )
    op.create_index("ix_course_instructors_course_id", "course_instructors", ["course_id"])
    op.create_index("ix_course_instructors_instructor_id", "course_instructors", ["instructor_id"])

    op.create_table(
        "cohort_instructors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instructor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_label", sa.String(length=80), nullable=False, server_default="Instructor"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["cohort_id"], ["cohorts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["instructor_id"], ["instructor_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cohort_id", "instructor_id", name="uq_cohort_instructors_cohort_instructor"),
    )
    op.create_index("ix_cohort_instructors_cohort_id", "cohort_instructors", ["cohort_id"])
    op.create_index("ix_cohort_instructors_instructor_id", "cohort_instructors", ["instructor_id"])


def downgrade() -> None:
    op.drop_index("ix_cohort_instructors_instructor_id", table_name="cohort_instructors")
    op.drop_index("ix_cohort_instructors_cohort_id", table_name="cohort_instructors")
    op.drop_table("cohort_instructors")
    op.drop_index("ix_course_instructors_instructor_id", table_name="course_instructors")
    op.drop_index("ix_course_instructors_course_id", table_name="course_instructors")
    op.drop_table("course_instructors")
    op.drop_table("instructor_profiles")
