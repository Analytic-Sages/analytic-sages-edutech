"""Hackathon details, challenge type, source role

Revision ID: 018_hackathon_intelligence
Revises: 017_opportunity_intelligence
Create Date: 2026-09-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "018_hackathon_intelligence"
down_revision: Union[str, None] = "017_opportunity_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE opportunity_type ADD VALUE IF NOT EXISTS 'challenge'")

    op.execute(
        "CREATE TYPE hackathon_event_format AS ENUM "
        "('online', 'in_person', 'hybrid', 'unknown')"
    )
    op.execute(
        "CREATE TYPE opportunity_source_role AS ENUM "
        "('direct', 'discovery', 'aggregator', 'manual')"
    )

    event_format = postgresql.ENUM(
        "online",
        "in_person",
        "hybrid",
        "unknown",
        name="hackathon_event_format",
        create_type=False,
    )
    source_role = postgresql.ENUM(
        "direct",
        "discovery",
        "aggregator",
        "manual",
        name="opportunity_source_role",
        create_type=False,
    )

    op.add_column(
        "opportunity_sources",
        sa.Column("source_role", source_role, nullable=False, server_default="direct"),
    )
    op.add_column(
        "opportunity_sources",
        sa.Column(
            "capabilities",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(
                "'{\"supports_automation\": false, \"supports_api\": false, "
                "\"supports_rss\": false, \"supports_search\": false, "
                "\"requires_review\": true}'::jsonb"
            ),
        ),
    )

    op.create_table(
        "opportunity_hackathon_details",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("short_description", sa.String(length=500), nullable=True),
        sa.Column("registration_url", sa.String(length=500), nullable=True),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("registration_open_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("registration_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submission_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("announcement_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_format", event_format, nullable=False, server_default="unknown"),
        sa.Column("prize_pool_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("prize_currency", sa.String(length=8), nullable=True),
        sa.Column("prize_pool_raw", sa.String(length=255), nullable=True),
        sa.Column("team_size_min", sa.Integer(), nullable=True),
        sa.Column("team_size_max", sa.Integer(), nullable=True),
        sa.Column("team_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("individual_allowed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "tracks",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("technology_focus", sa.String(length=255), nullable=True),
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
        "ix_opportunity_hackathon_details_registration_deadline",
        "opportunity_hackathon_details",
        ["registration_deadline"],
    )
    op.create_index(
        "ix_opportunity_hackathon_details_start_at",
        "opportunity_hackathon_details",
        ["start_at"],
    )
    op.create_index(
        "ix_opportunity_hackathon_details_derived_phase",
        "opportunity_hackathon_details",
        ["derived_phase"],
    )

    # Mark known hackathon platforms
    op.execute(
        """
        UPDATE opportunity_sources
        SET source_role = 'direct',
            capabilities = jsonb_build_object(
              'supports_automation', true,
              'supports_api', connector_type IN ('colosseum', 'devfolio', 'superteam', 'encode'),
              'supports_rss', false,
              'supports_html', connector_type IN ('ethglobal', 'devpost', 'dorahacks', 'encode'),
              'supports_search', false,
              'requires_review', true
            )
        WHERE connector_type IN (
          'ethglobal', 'colosseum', 'devpost', 'devfolio', 'dorahacks', 'encode', 'superteam'
        )
        """
    )


def downgrade() -> None:
    op.drop_table("opportunity_hackathon_details")
    op.drop_column("opportunity_sources", "capabilities")
    op.drop_column("opportunity_sources", "source_role")
    op.execute("DROP TYPE opportunity_source_role")
    op.execute("DROP TYPE hackathon_event_format")
    # Cannot easily remove enum value 'challenge' from opportunity_type
