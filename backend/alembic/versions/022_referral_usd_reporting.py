"""USD reporting fields + fraud_status for referral programme

Revision ID: 022_referral_usd_reporting
Revises: 021_referral_partner_program
Create Date: 2026-09-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "022_referral_usd_reporting"
down_revision: Union[str, None] = "021_referral_partner_program"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE referral_fraud_status AS ENUM "
        "('clear', 'flagged', 'review_required')"
    )
    fraud_status = postgresql.ENUM(
        "clear",
        "flagged",
        "review_required",
        name="referral_fraud_status",
        create_type=False,
    )

    op.add_column(
        "referral_conversions",
        sa.Column(
            "fraud_status",
            fraud_status,
            nullable=False,
            server_default="clear",
        ),
    )
    op.add_column(
        "referral_conversions",
        sa.Column("reporting_fx_rate", sa.Numeric(18, 8), nullable=True),
    )
    op.add_column(
        "referral_conversions",
        sa.Column("reporting_fx_timestamp", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "referral_conversions",
        sa.Column("reporting_usd_equivalent", sa.Numeric(12, 2), nullable=True),
    )

    op.add_column(
        "partner_ledger_entries",
        sa.Column("reporting_fx_rate", sa.Numeric(18, 8), nullable=True),
    )
    op.add_column(
        "partner_ledger_entries",
        sa.Column("reporting_fx_timestamp", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "partner_ledger_entries",
        sa.Column("reporting_usd_equivalent", sa.Numeric(12, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("partner_ledger_entries", "reporting_usd_equivalent")
    op.drop_column("partner_ledger_entries", "reporting_fx_timestamp")
    op.drop_column("partner_ledger_entries", "reporting_fx_rate")
    op.drop_column("referral_conversions", "reporting_usd_equivalent")
    op.drop_column("referral_conversions", "reporting_fx_timestamp")
    op.drop_column("referral_conversions", "reporting_fx_rate")
    op.drop_column("referral_conversions", "fraud_status")
    op.execute("DROP TYPE referral_fraud_status")
