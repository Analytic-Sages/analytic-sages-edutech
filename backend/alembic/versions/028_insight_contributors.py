"""Add contributors to Insights articles.

Revision ID: 028_insight_contributors
Revises: 027_insight_content_type
Create Date: 2026-09-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "028_insight_contributors"
down_revision: Union[str, None] = "027_insight_content_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "article_contributors",
        sa.Column("article_id", sa.UUID(), nullable=False),
        sa.Column("author_profile_id", sa.UUID(), nullable=False),
        sa.Column("contribution_role", sa.String(length=120), nullable=False, server_default="Contributor"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_profile_id"], ["author_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("article_id", "author_profile_id"),
    )


def downgrade() -> None:
    op.drop_table("article_contributors")