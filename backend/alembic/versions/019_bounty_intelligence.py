"""Bounty details and discovery source metadata

Revision ID: 019_bounty_intelligence
Revises: 018_hackathon_intelligence
Create Date: 2026-09-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "019_bounty_intelligence"
down_revision: Union[str, None] = "018_hackathon_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE bounty_category AS ENUM "
        "('bug', 'security', 'development', 'content', 'design', 'research', 'quest', 'other', 'unknown')"
    )
    category = postgresql.ENUM(
        "bug",
        "security",
        "development",
        "content",
        "design",
        "research",
        "quest",
        "other",
        "unknown",
        name="bounty_category",
        create_type=False,
    )

    op.create_table(
        "opportunity_bounty_details",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("short_description", sa.String(length=500), nullable=True),
        sa.Column("listing_url", sa.String(length=500), nullable=True),
        sa.Column("reward_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("reward_token", sa.String(length=32), nullable=True),
        sa.Column("reward_currency", sa.String(length=8), nullable=True),
        sa.Column("reward_raw", sa.String(length=255), nullable=True),
        sa.Column("reward_min", sa.Numeric(14, 2), nullable=True),
        sa.Column("reward_max", sa.Numeric(14, 2), nullable=True),
        sa.Column("category", category, nullable=False, server_default="unknown"),
        sa.Column("opens_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("winners_announced", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("skills", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("chain_focus", sa.String(length=120), nullable=True),
        sa.Column("derived_phase", sa.String(length=20), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("opportunity_id"),
    )
    op.create_index(
        "ix_opportunity_bounty_details_deadline",
        "opportunity_bounty_details",
        ["deadline"],
    )
    op.create_index(
        "ix_opportunity_bounty_details_derived_phase",
        "opportunity_bounty_details",
        ["derived_phase"],
    )
    op.create_index(
        "ix_opportunity_bounty_details_category",
        "opportunity_bounty_details",
        ["category"],
    )

    # Mark Superteam as primary automated bounty+earn source; Pond stays discovery
    op.execute(
        """
        UPDATE opportunity_sources
        SET capabilities = COALESCE(capabilities, '{}'::jsonb) || jsonb_build_object(
              'supports_bounties', true,
              'supports_automation', true,
              'requires_review', true
            )
        WHERE connector_type = 'superteam'
        """
    )
    op.execute(
        """
        UPDATE opportunity_sources
        SET source_role = 'discovery',
            capabilities = COALESCE(capabilities, '{}'::jsonb) || jsonb_build_object(
              'supports_bounties', true,
              'supports_automation', false,
              'requires_review', true
            ),
            admin_notes = COALESCE(NULLIF(admin_notes, ''), '') ||
              CASE WHEN admin_notes ILIKE '%bounty%' THEN ''
                   ELSE E'\nBounty discovery board — manual review only until an official API is approved.'
              END
        WHERE lower(name) = 'pond'
        """
    )


def downgrade() -> None:
    op.drop_table("opportunity_bounty_details")
    op.execute("DROP TYPE bounty_category")
