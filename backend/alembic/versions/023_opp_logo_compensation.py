"""Add organization logo and compensation text to opportunities

Revision ID: 023_opp_logo_compensation
Revises: 022_referral_usd_reporting
Create Date: 2026-09-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "023_opp_logo_compensation"
down_revision: Union[str, None] = "022_referral_usd_reporting"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Idempotent: previous deploy may have added columns before version_num
    # write failed (revision id was > varchar(32)).
    bind = op.get_bind()
    existing = {col["name"] for col in sa.inspect(bind).get_columns("opportunities")}
    if "organization_logo_url" not in existing:
        op.add_column(
            "opportunities",
            sa.Column("organization_logo_url", sa.String(length=500), nullable=True),
        )
    if "compensation_text" not in existing:
        op.add_column(
            "opportunities",
            sa.Column("compensation_text", sa.String(length=255), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    existing = {col["name"] for col in sa.inspect(bind).get_columns("opportunities")}
    if "compensation_text" in existing:
        op.drop_column("opportunities", "compensation_text")
    if "organization_logo_url" in existing:
        op.drop_column("opportunities", "organization_logo_url")
