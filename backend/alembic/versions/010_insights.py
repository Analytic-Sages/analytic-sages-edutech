"""Insights articles, author profiles, and editorial roles

Revision ID: 010_insights
Revises: 009_instructor_profiles
Create Date: 2026-08-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_insights"
down_revision: Union[str, None] = "009_instructor_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'editor'")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'author'")
    article_status = postgresql.ENUM(
        "draft",
        "pending_review",
        "published",
        "archived",
        name="article_status",
    )
    article_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "author_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("bio", sa.Text(), nullable=False, server_default=""),
        sa.Column("photo_url", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False, server_default=""),
        sa.Column("cover_image_url", sa.String(length=512), nullable=True),
        sa.Column("category", sa.String(length=40), nullable=False, server_default="Education"),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column(
            "body",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft",
                "pending_review",
                "published",
                "archived",
                name="article_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("byline_name", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("byline_title", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("seo_title", sa.String(length=200), nullable=True),
        sa.Column("seo_description", sa.String(length=320), nullable=True),
        sa.Column("og_image_url", sa.String(length=512), nullable=True),
        sa.Column("featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("read_time_minutes", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["author_profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_articles_slug", "articles", ["slug"], unique=True)
    op.create_index("ix_articles_author_id", "articles", ["author_id"])


def downgrade() -> None:
    op.drop_index("ix_articles_author_id", table_name="articles")
    op.drop_index("ix_articles_slug", table_name="articles")
    op.drop_table("articles")
    op.drop_table("author_profiles")
    postgresql.ENUM(name="article_status").drop(op.get_bind(), checkfirst=True)
