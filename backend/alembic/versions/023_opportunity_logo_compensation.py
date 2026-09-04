"""Add organization logo and compensation text to opportunities

Revision ID: 023_opportunity_logo_compensation
Revises: 022_referral_usd_reporting
Create Date: 2026-09-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "023_opportunity_logo_compensation"
down_revision: Union[str, None] = "022_referral_usd_reporting"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "opportunities",
        sa.Column("organization_logo_url", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "opportunities",
        sa.Column("compensation_text", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("opportunities", "compensation_text")
    op.drop_column("opportunities", "organization_logo_url")
