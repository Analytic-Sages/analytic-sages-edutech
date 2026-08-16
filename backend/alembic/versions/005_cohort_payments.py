"""Cohort pricing + payment.cohort_id

Revision ID: 005_cohort_payments
Revises: 004_cohort_deadline
Create Date: 2026-08-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_cohort_payments"
down_revision: Union[str, None] = "004_cohort_deadline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cohorts",
        sa.Column("price", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "cohorts",
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
    )

    op.add_column(
        "payments",
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_payments_cohort_id_cohorts",
        "payments",
        "cohorts",
        ["cohort_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_payments_cohort_id", "payments", ["cohort_id"])

    # Course-only payments remain valid; cohort payments may omit course_id.
    op.alter_column("payments", "course_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)


def downgrade() -> None:
    op.execute("UPDATE payments SET course_id = (SELECT id FROM courses LIMIT 1) WHERE course_id IS NULL")
    op.alter_column("payments", "course_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    op.drop_index("ix_payments_cohort_id", table_name="payments")
    op.drop_constraint("fk_payments_cohort_id_cohorts", "payments", type_="foreignkey")
    op.drop_column("payments", "cohort_id")
    op.drop_column("cohorts", "currency")
    op.drop_column("cohorts", "price")
