"""Opportunity intelligence: source metadata, match reasons, location scope, dedupe

Revision ID: 017_opportunity_intelligence
Revises: 016_tuition_billing
Create Date: 2026-09-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "017_opportunity_intelligence"
down_revision: Union[str, None] = "016_tuition_billing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE location_scope AS ENUM "
        "('worldwide', 'global', 'africa', 'europe', 'emea', 'north_america', "
        "'us_only', 'uk_only', 'other', 'unknown')"
    )
    location_scope = postgresql.ENUM(
        "worldwide",
        "global",
        "africa",
        "europe",
        "emea",
        "north_america",
        "us_only",
        "uk_only",
        "other",
        "unknown",
        name="location_scope",
        create_type=False,
    )

    op.add_column(
        "opportunity_sources",
        sa.Column("base_url", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "opportunity_sources",
        sa.Column("sync_frequency_hours", sa.Integer(), nullable=False, server_default="6"),
    )
    op.add_column(
        "opportunity_sources",
        sa.Column("attribution_required", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "opportunity_sources",
        sa.Column("admin_notes", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "opportunity_sources",
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "opportunity_sources",
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "opportunity_sources",
        sa.Column(
            "search_profiles",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    # Trust-first: never auto-publish external listings.
    op.execute("UPDATE opportunity_sources SET auto_publish_allowed = false")

    op.add_column(
        "opportunities",
        sa.Column("location_raw", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "opportunities",
        sa.Column("location_scope", location_scope, nullable=True),
    )
    op.add_column(
        "opportunities",
        sa.Column("canonical_application_url", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "opportunities",
        sa.Column(
            "match_reasons",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "opportunities",
        sa.Column(
            "matched_career_tracks",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "opportunities",
        sa.Column("duplicate_confidence", sa.String(length=20), nullable=True),
    )
    op.create_index(
        "ix_opportunities_canonical_application_url",
        "opportunities",
        ["canonical_application_url"],
    )
    op.create_index("ix_opportunities_relevance_score", "opportunities", ["relevance_score"])
    op.create_index("ix_opportunities_workplace_type", "opportunities", ["workplace_type"])
    op.create_index("ix_opportunities_employment_type", "opportunities", ["employment_type"])


def downgrade() -> None:
    op.drop_index("ix_opportunities_employment_type", table_name="opportunities")
    op.drop_index("ix_opportunities_workplace_type", table_name="opportunities")
    op.drop_index("ix_opportunities_relevance_score", table_name="opportunities")
    op.drop_index("ix_opportunities_canonical_application_url", table_name="opportunities")
    op.drop_column("opportunities", "duplicate_confidence")
    op.drop_column("opportunities", "matched_career_tracks")
    op.drop_column("opportunities", "match_reasons")
    op.drop_column("opportunities", "canonical_application_url")
    op.drop_column("opportunities", "location_scope")
    op.drop_column("opportunities", "location_raw")
    op.drop_column("opportunity_sources", "search_profiles")
    op.drop_column("opportunity_sources", "last_failure_at")
    op.drop_column("opportunity_sources", "last_success_at")
    op.drop_column("opportunity_sources", "admin_notes")
    op.drop_column("opportunity_sources", "attribution_required")
    op.drop_column("opportunity_sources", "sync_frequency_hours")
    op.drop_column("opportunity_sources", "base_url")
    op.execute("DROP TYPE location_scope")
