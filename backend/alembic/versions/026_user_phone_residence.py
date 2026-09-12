"""Add optional phone and country of residence on users.

Revision ID: 026_user_phone_residence
Revises: 025_event_keep_learning
Create Date: 2026-09-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "026_user_phone_residence"
down_revision: Union[str, None] = "025_event_keep_learning"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.String(32), nullable=True))
    op.add_column("users", sa.Column("phone_country_code", sa.String(2), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "phone_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column("users", sa.Column("country_of_residence", sa.String(2), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "country_of_residence")
    op.drop_column("users", "phone_verified")
    op.drop_column("users", "phone_country_code")
    op.drop_column("users", "phone_number")
