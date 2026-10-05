"""Assignments and submissions for live cohorts.

Revision ID: 034_assignments
Revises: 033_live_programmes
Create Date: 2026-10-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "034_assignments"
down_revision: Union[str, None] = "033_live_programmes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE assignment_status AS ENUM ('draft', 'published', 'archived')")
    op.execute(
        "CREATE TYPE submission_status AS ENUM "
        "('draft', 'submitted', 'under_review', 'reviewed', 'returned', 'late', 'missing')"
    )

    assignment_status = postgresql.ENUM(
        "draft", "published", "archived", name="assignment_status", create_type=False
    )
    submission_status = postgresql.ENUM(
        "draft", "submitted", "under_review", "reviewed", "returned", "late", "missing",
        name="submission_status", create_type=False,
    )

    op.create_table(
        "assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("week_label", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_score", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("passing_score", sa.Integer(), nullable=True),
        sa.Column("required_fields", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("resources", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", assignment_status, nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["cohort_id"], ["cohorts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["live_sessions.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_assignments_cohort_id", "assignments", ["cohort_id"])
    op.create_index("ix_assignments_session_id", "assignments", ["session_id"])
    op.create_index("ix_assignments_status", "assignments", ["status"])
    op.create_index("ix_assignments_due_date", "assignments", ["due_date"])

    op.create_table(
        "assignment_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", submission_status, nullable=False, server_default="draft"),
        sa.Column("text_response", sa.Text(), nullable=True),
        sa.Column("github_url", sa.String(length=512), nullable=True),
        sa.Column("live_url", sa.String(length=512), nullable=True),
        sa.Column("build_in_public_url", sa.String(length=512), nullable=True),
        sa.Column("documentation_url", sa.String(length=512), nullable=True),
        sa.Column("files", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("assignment_id", "user_id", name="uq_assignment_submissions_assignment_user"),
    )
    op.create_index("ix_assignment_submissions_assignment_id", "assignment_submissions", ["assignment_id"])
    op.create_index("ix_assignment_submissions_user_id", "assignment_submissions", ["user_id"])
    op.create_index("ix_assignment_submissions_status", "assignment_submissions", ["status"])


def downgrade() -> None:
    op.drop_table("assignment_submissions")
    op.drop_table("assignments")
    op.execute("DROP TYPE submission_status")
    op.execute("DROP TYPE assignment_status")
