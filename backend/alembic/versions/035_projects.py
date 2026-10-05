"""Student projects within live cohorts.

Revision ID: 035_projects
Revises: 034_assignments
Create Date: 2026-10-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "035_projects"
down_revision: Union[str, None] = "034_assignments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE project_status AS ENUM "
        "('planned', 'in_progress', 'submitted', 'reviewed', 'completed')"
    )

    project_status = postgresql.ENUM(
        "planned", "in_progress", "submitted", "reviewed", "completed",
        name="project_status", create_type=False,
    )

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", project_status, nullable=False, server_default="planned"),
        sa.Column("github_url", sa.String(length=512), nullable=True),
        sa.Column("live_url", sa.String(length=512), nullable=True),
        sa.Column("build_in_public_url", sa.String(length=512), nullable=True),
        sa.Column("documentation_url", sa.String(length=512), nullable=True),
        sa.Column("cover_image", sa.String(length=512), nullable=True),
        sa.Column("technologies", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["cohort_id"], ["cohorts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_projects_cohort_id", "projects", ["cohort_id"])
    op.create_index("ix_projects_user_id", "projects", ["user_id"])
    op.create_index("ix_projects_status", "projects", ["status"])


def downgrade() -> None:
    op.drop_table("projects")
    op.execute("DROP TYPE project_status")
