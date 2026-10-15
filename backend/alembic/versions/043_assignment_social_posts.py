"""Track X and LinkedIn Build in Public drafts and published posts.

Revision ID: 043_assignment_social_posts
Revises: 042_payment_amount_integrity
Create Date: 2026-10-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "043_assignment_social_posts"
down_revision: Union[str, None] = "042_payment_amount_integrity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("assignment_submissions", sa.Column("x_post_text", sa.Text(), nullable=True))
    op.add_column("assignment_submissions", sa.Column("x_post_url", sa.String(length=512), nullable=True))
    op.add_column("assignment_submissions", sa.Column("linkedin_post_text", sa.Text(), nullable=True))
    op.add_column("assignment_submissions", sa.Column("linkedin_post_url", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("assignment_submissions", "linkedin_post_url")
    op.drop_column("assignment_submissions", "linkedin_post_text")
    op.drop_column("assignment_submissions", "x_post_url")
    op.drop_column("assignment_submissions", "x_post_text")
