"""Add cohort registration_deadline

Revision ID: 004_cohort_deadline
Revises: 003_classroom
Create Date: 2026-08-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_cohort_deadline"
down_revision: Union[str, None] = "003_classroom"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cohorts",
        sa.Column("registration_deadline", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cohorts", "registration_deadline")
