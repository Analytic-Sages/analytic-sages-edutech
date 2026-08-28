"""Opportunities P2/P3: saves, career interests, Telegram/digest metadata

Revision ID: 014_opportunity_engagement
Revises: 013_opportunity_ingestion
Create Date: 2026-08-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "014_opportunity_engagement"
down_revision: Union[str, None] = "013_opportunity_ingestion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE opportunity_save_state AS ENUM ('saved', 'applied')")
    save_state = postgresql.ENUM("saved", "applied", name="opportunity_save_state", create_type=False)

    op.add_column("opportunities", sa.Column("telegram_announced_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "opportunities",
        sa.Column("review_assist", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    )

    op.create_table(
        "opportunity_saves",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "opportunity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state", save_state, nullable=False, server_default="saved"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_opportunity_saves_user_id", "opportunity_saves", ["user_id"])
    op.create_index("ix_opportunity_saves_opportunity_id", "opportunity_saves", ["opportunity_id"])
    op.create_unique_constraint("uq_opportunity_saves_user", "opportunity_saves", ["user_id", "opportunity_id"])

    op.create_table(
        "user_career_interests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "career_path_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("career_paths.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_career_interests_user_id", "user_career_interests", ["user_id"])
    op.create_index("ix_user_career_interests_career_path_id", "user_career_interests", ["career_path_id"])
    op.create_unique_constraint("uq_user_career_interests", "user_career_interests", ["user_id", "career_path_id"])

    op.create_table(
        "opportunity_digest_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("listing_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("item_ids", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="sent"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("triggered_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("opportunity_digest_runs")
    op.drop_table("user_career_interests")
    op.drop_table("opportunity_saves")
    op.drop_column("opportunities", "review_assist")
    op.drop_column("opportunities", "telegram_announced_at")
    op.execute("DROP TYPE opportunity_save_state")
