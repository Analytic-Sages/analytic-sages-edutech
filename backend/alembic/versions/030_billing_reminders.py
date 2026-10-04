"""Track installment reminder emails.

Revision ID: 030_billing_reminders
Revises: 029_live_session_type
Create Date: 2026-10-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "030_billing_reminders"
down_revision: Union[str, None] = "029_live_session_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "payment_obligations",
        sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("payment_obligations", "reminder_sent_at")