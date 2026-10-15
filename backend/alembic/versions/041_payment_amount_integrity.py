"""Track expected and settled provider payment amounts.

Revision ID: 041_payment_amount_integrity
Revises: 040_recording_import
Create Date: 2026-10-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "041_payment_amount_integrity"
down_revision: Union[str, None] = "039_realtimekit_attendance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "payments",
        sa.Column("charge_amount", sa.Numeric(14, 2), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("charge_currency", sa.String(length=3), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("settled_amount", sa.Numeric(14, 2), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("settled_currency", sa.String(length=3), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("payments", "settled_currency")
    op.drop_column("payments", "settled_amount")
    op.drop_column("payments", "charge_currency")
    op.drop_column("payments", "charge_amount")
