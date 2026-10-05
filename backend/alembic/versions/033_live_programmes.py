"""Live programmes, cohort enrichment, attendance and student profile links.

Revision ID: 033_live_programmes
Revises: 032_student_access_grants
Create Date: 2026-10-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "033_live_programmes"
down_revision: Union[str, None] = "032_student_access_grants"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE programme_status AS ENUM "
        "('draft', 'upcoming', 'active', 'completed', 'archived')"
    )
    op.execute(
        "CREATE TYPE cohort_enrollment_status AS ENUM "
        "('pending', 'active', 'completed', 'withdrawn', 'suspended')"
    )
    op.execute("CREATE TYPE attendance_status AS ENUM ('attended', 'late', 'absent')")

    programme_status = postgresql.ENUM(
        "draft", "upcoming", "active", "completed", "archived",
        name="programme_status", create_type=False,
    )
    cohort_enrollment_status = postgresql.ENUM(
        "pending", "active", "completed", "withdrawn", "suspended",
        name="cohort_enrollment_status", create_type=False,
    )
    attendance_status = postgresql.ENUM(
        "attended", "late", "absent", name="attendance_status", create_type=False,
    )

    op.create_table(
        "programmes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("overview", sa.Text(), nullable=False, server_default=""),
        sa.Column("learning_outcomes", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("duration", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("programme_type", sa.String(length=40), nullable=False, server_default="live"),
        sa.Column("status", programme_status, nullable=False, server_default="draft"),
        sa.Column("cover_image", sa.String(length=512), nullable=True),
        sa.Column("requirements", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("certificate_requirements", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False,
        ),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("slug", name="uq_programmes_slug"),
    )
    op.create_index("ix_programmes_status", "programmes", ["status"])
    op.create_index("ix_programmes_course_id", "programmes", ["course_id"])


    op.create_table(
        "attendance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", attendance_status, nullable=False, server_default="attended"),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["live_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("session_id", "user_id", name="uq_attendance_session_user"),
    )
    op.create_index("ix_attendance_session_id", "attendance", ["session_id"])
    op.create_index("ix_attendance_user_id", "attendance", ["user_id"])
    op.create_index("ix_attendance_status", "attendance", ["status"])

    op.add_column("cohorts", sa.Column("programme_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("cohorts", sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"))
    op.add_column("cohorts", sa.Column("capacity", sa.Integer(), nullable=True))
    op.add_column(
        "cohorts",
        sa.Column("community_links", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column(
        "cohorts",
        sa.Column("enrollment_settings", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_foreign_key(
        "fk_cohorts_programme_id_programmes", "cohorts", "programmes",
        ["programme_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index("ix_cohorts_programme_id", "cohorts", ["programme_id"])

    op.add_column(
        "cohort_members",
        sa.Column("enrollment_status", cohort_enrollment_status, nullable=False, server_default="active"),
    )
    op.add_column("cohort_members", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "cohort_members",
        sa.Column("certificate_eligible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("cohort_members", sa.Column("source", sa.String(length=80), nullable=True))
    op.create_index(
        "ix_cohort_members_cohort_status", "cohort_members", ["cohort_id", "enrollment_status"],
    )

    op.add_column("live_sessions", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "live_sessions", sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
    )
    op.add_column("live_sessions", sa.Column("meeting_url", sa.String(length=512), nullable=True))
    op.add_column("live_sessions", sa.Column("instructor_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_live_sessions_instructor_user_id_users", "live_sessions", "users",
        ["instructor_user_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index("ix_live_sessions_instructor_user_id", "live_sessions", ["instructor_user_id"])

    op.add_column("users", sa.Column("discord_username", sa.String(length=80), nullable=True))
    op.add_column("users", sa.Column("telegram_username", sa.String(length=80), nullable=True))
    op.add_column("users", sa.Column("github_url", sa.String(length=512), nullable=True))
    op.add_column("users", sa.Column("x_url", sa.String(length=512), nullable=True))
    op.add_column("users", sa.Column("linkedin_url", sa.String(length=512), nullable=True))
    op.add_column("users", sa.Column("portfolio_url", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "portfolio_url")
    op.drop_column("users", "linkedin_url")
    op.drop_column("users", "x_url")
    op.drop_column("users", "github_url")
    op.drop_column("users", "telegram_username")
    op.drop_column("users", "discord_username")

    op.drop_index("ix_live_sessions_instructor_user_id", table_name="live_sessions")
    op.drop_constraint("fk_live_sessions_instructor_user_id_users", "live_sessions", type_="foreignkey")
    op.drop_column("live_sessions", "instructor_user_id")
    op.drop_column("live_sessions", "meeting_url")
    op.drop_column("live_sessions", "timezone")
    op.drop_column("live_sessions", "description")

    op.drop_index("ix_cohort_members_cohort_status", table_name="cohort_members")
    op.drop_column("cohort_members", "source")
    op.drop_column("cohort_members", "certificate_eligible")
    op.drop_column("cohort_members", "completed_at")
    op.drop_column("cohort_members", "enrollment_status")

    op.drop_index("ix_cohorts_programme_id", table_name="cohorts")
    op.drop_constraint("fk_cohorts_programme_id_programmes", "cohorts", type_="foreignkey")
    op.drop_column("cohorts", "enrollment_settings")
    op.drop_column("cohorts", "community_links")
    op.drop_column("cohorts", "capacity")
    op.drop_column("cohorts", "timezone")
    op.drop_column("cohorts", "programme_id")

    op.drop_table("attendance")
    op.drop_table("programmes")
    op.execute("DROP TYPE attendance_status")
    op.execute("DROP TYPE cohort_enrollment_status")
    op.execute("DROP TYPE programme_status")
