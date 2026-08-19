"""Self-paced modules, lessons, and lesson progress

Revision ID: 006_self_paced_lms
Revises: 005_cohort_payments
Create Date: 2026-08-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_self_paced_lms"
down_revision: Union[str, None] = "005_cohort_payments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE enrollment_status ADD VALUE IF NOT EXISTS 'completed'")

    op.add_column(
        "courses",
        sa.Column("long_description", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "courses",
        sa.Column("estimated_minutes", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "courses",
        sa.Column("delivery_type", sa.String(length=32), nullable=False, server_default="self_paced"),
    )
    op.add_column(
        "courses",
        sa.Column("is_free", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "courses",
        sa.Column("certificate_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )

    op.add_column("enrollments", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "enrollments",
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "course_modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("order_index", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "order_index", name="uq_course_modules_course_order"),
    )
    op.create_index("ix_course_modules_course_id", "course_modules", ["course_id"])

    op.create_table(
        "lessons",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("subtitle", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("video_provider", sa.String(length=40), nullable=False, server_default="youtube"),
        sa.Column("video_id", sa.String(length=80), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "what_you_learn",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "key_concepts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "resources",
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
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["course_modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "slug", name="uq_lessons_course_slug"),
        sa.UniqueConstraint("module_id", "order_index", name="uq_lessons_module_order"),
    )
    op.create_index("ix_lessons_course_id", "lessons", ["course_id"])
    op.create_index("ix_lessons_module_id", "lessons", ["module_id"])

    op.create_table(
        "lesson_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrollment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_viewed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("enrollment_id", "lesson_id", name="uq_lesson_progress_enrollment_lesson"),
    )
    op.create_index("ix_lesson_progress_enrollment_id", "lesson_progress", ["enrollment_id"])
    op.create_index("ix_lesson_progress_lesson_id", "lesson_progress", ["lesson_id"])


def downgrade() -> None:
    op.drop_index("ix_lesson_progress_lesson_id", table_name="lesson_progress")
    op.drop_index("ix_lesson_progress_enrollment_id", table_name="lesson_progress")
    op.drop_table("lesson_progress")
    op.drop_index("ix_lessons_module_id", table_name="lessons")
    op.drop_index("ix_lessons_course_id", table_name="lessons")
    op.drop_table("lessons")
    op.drop_index("ix_course_modules_course_id", table_name="course_modules")
    op.drop_table("course_modules")
    op.drop_column("enrollments", "last_activity_at")
    op.drop_column("enrollments", "completed_at")
    op.drop_column("courses", "certificate_enabled")
    op.drop_column("courses", "is_free")
    op.drop_column("courses", "delivery_type")
    op.drop_column("courses", "estimated_minutes")
    op.drop_column("courses", "long_description")
