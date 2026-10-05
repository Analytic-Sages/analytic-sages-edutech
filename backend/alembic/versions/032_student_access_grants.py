"""Student access controls + course access grants.

Revision ID: 032_student_access_grants
Revises: 031_quizzes
Create Date: 2026-10-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "032_student_access_grants"
down_revision: Union[str, None] = "031_quizzes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "student_billing_accounts",
        sa.Column(
            "access_blocked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.create_table(
        "course_access_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_label", sa.String(length=80), nullable=False, server_default="Instructor"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "course_id", name="uq_course_access_grants_user_course"),
    )
    op.create_index("ix_course_access_grants_user_id", "course_access_grants", ["user_id"])
    op.create_index("ix_course_access_grants_course_id", "course_access_grants", ["course_id"])


def downgrade() -> None:
    op.drop_table("course_access_grants")
    op.drop_column("student_billing_accounts", "access_blocked")
