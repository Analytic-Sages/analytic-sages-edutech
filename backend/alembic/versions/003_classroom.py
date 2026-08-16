"""Classroom: cohorts, members, live sessions

Revision ID: 003_classroom
Revises: 002_payments
Create Date: 2026-08-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_classroom"
down_revision: Union[str, None] = "002_payments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE cohort_status AS ENUM ('draft', 'open', 'active', 'completed')")
    op.execute("CREATE TYPE cohort_member_role AS ENUM ('student', 'instructor', 'ta')")
    op.execute(
        "CREATE TYPE live_session_status AS ENUM ('scheduled', 'live', 'ended', 'cancelled')"
    )

    cohort_status = postgresql.ENUM(
        "draft", "open", "active", "completed", name="cohort_status", create_type=False
    )
    cohort_member_role = postgresql.ENUM(
        "student", "instructor", "ta", name="cohort_member_role", create_type=False
    )
    live_session_status = postgresql.ENUM(
        "scheduled", "live", "ended", "cancelled", name="live_session_status", create_type=False
    )

    op.create_table(
        "cohorts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", cohort_status, nullable=False, server_default="draft"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_cohorts_slug", "cohorts", ["slug"], unique=True)
    op.create_index("ix_cohorts_course_id", "cohorts", ["course_id"])

    op.create_table(
        "cohort_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", cohort_member_role, nullable=False, server_default="student"),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["cohort_id"], ["cohorts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("cohort_id", "user_id", name="uq_cohort_members_cohort_user"),
    )
    op.create_index("ix_cohort_members_cohort_id", "cohort_members", ["cohort_id"])
    op.create_index("ix_cohort_members_user_id", "cohort_members", ["user_id"])

    op.create_table(
        "live_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("week_label", sa.String(80), nullable=False, server_default=""),
        sa.Column("session_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "objectives",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "resources",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("assignment_summary", sa.Text(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", live_session_status, nullable=False, server_default="scheduled"),
        sa.Column("realtimekit_meeting_id", sa.String(64), nullable=True),
        sa.Column("recording_url", sa.String(512), nullable=True),
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
        sa.ForeignKeyConstraint(["cohort_id"], ["cohorts.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_live_sessions_cohort_id", "live_sessions", ["cohort_id"])
    op.create_index("ix_live_sessions_starts_at", "live_sessions", ["starts_at"])


def downgrade() -> None:
    op.drop_index("ix_live_sessions_starts_at", table_name="live_sessions")
    op.drop_index("ix_live_sessions_cohort_id", table_name="live_sessions")
    op.drop_table("live_sessions")
    op.drop_index("ix_cohort_members_user_id", table_name="cohort_members")
    op.drop_index("ix_cohort_members_cohort_id", table_name="cohort_members")
    op.drop_table("cohort_members")
    op.drop_index("ix_cohorts_course_id", table_name="cohorts")
    op.drop_index("ix_cohorts_slug", table_name="cohorts")
    op.drop_table("cohorts")
    op.execute("DROP TYPE live_session_status")
    op.execute("DROP TYPE cohort_member_role")
    op.execute("DROP TYPE cohort_status")
