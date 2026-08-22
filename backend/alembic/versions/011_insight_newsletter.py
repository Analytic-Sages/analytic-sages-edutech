"""Send Insights newsletters once; skip existing published posts

Revision ID: 011_insight_newsletter
Revises: 010_insights
Create Date: 2026-08-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011_insight_newsletter"
down_revision: Union[str, None] = "010_insights"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("newsletter_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        """
        UPDATE articles
        SET newsletter_sent_at = COALESCE(published_at, now())
        WHERE status = 'published'
        """
    )


def downgrade() -> None:
    op.drop_column("articles", "newsletter_sent_at")
