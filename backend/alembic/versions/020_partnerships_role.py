"""Add partnerships staff role for opportunities management

Revision ID: 020_partnerships_role
Revises: 019_bounty_intelligence
Create Date: 2026-09-04
"""

from typing import Sequence, Union

from alembic import op

revision: str = "020_partnerships_role"
down_revision: Union[str, None] = "019_bounty_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'partnerships'")


def downgrade() -> None:
    # Postgres cannot easily remove enum values
    pass
