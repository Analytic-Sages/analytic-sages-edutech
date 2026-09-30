"""Add content type to Insights articles.

Revision ID: 027_insight_content_type
Revises: 026_user_phone_residence
Create Date: 2026-09-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "027_insight_content_type"
down_revision: Union[str, None] = "026_user_phone_residence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("content_type", sa.String(length=30), nullable=False, server_default="Blog"),
    )


def downgrade() -> None:
    op.drop_column("articles", "content_type")