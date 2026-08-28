"""Opportunities P1: ingestion rows, sync runs, and risk flags

Revision ID: 013_opportunity_ingestion
Revises: 012_opportunities
Create Date: 2026-08-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "013_opportunity_ingestion"
down_revision: Union[str, None] = "012_opportunities"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE opportunity_ingestion_status AS ENUM "
        "('pending', 'processed', 'duplicate', 'rejected', 'failed')"
    )
    op.execute("CREATE TYPE opportunity_sync_run_status AS ENUM ('running', 'completed', 'failed')")
    op.execute(
        "CREATE TYPE opportunity_risk_flag_severity AS ENUM ('low', 'medium', 'high', 'critical')"
    )

    ingestion_status = postgresql.ENUM(
        "pending",
        "processed",
        "duplicate",
        "rejected",
        "failed",
        name="opportunity_ingestion_status",
        create_type=False,
    )
    sync_run_status = postgresql.ENUM(
        "running",
        "completed",
        "failed",
        name="opportunity_sync_run_status",
        create_type=False,
    )
    risk_severity = postgresql.ENUM(
        "low",
        "medium",
        "high",
        "critical",
        name="opportunity_risk_flag_severity",
        create_type=False,
    )

    op.add_column(
        "opportunity_sources",
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.add_column(
        "opportunities",
        sa.Column("is_manual", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column("opportunities", sa.Column("external_id", sa.String(length=255), nullable=True))
    op.add_column("opportunities", sa.Column("content_hash", sa.String(length=64), nullable=True))
    op.add_column("opportunities", sa.Column("relevance_score", sa.Numeric(5, 2), nullable=True))
    op.add_column(
        "opportunities",
        sa.Column("duplicate_of_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_opportunities_external_id", "opportunities", ["external_id"])
    op.create_index("ix_opportunities_duplicate_of_id", "opportunities", ["duplicate_of_id"])
    op.create_foreign_key(
        "fk_opportunities_duplicate_of_id",
        "opportunities",
        "opportunities",
        ["duplicate_of_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_opportunities_source_external "
        "ON opportunities (source_id, external_id) "
        "WHERE source_id IS NOT NULL AND external_id IS NOT NULL"
    )

    op.create_table(
        "opportunity_ingestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("raw_title", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("raw_content", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "raw_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("processing_status", ingestion_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["opportunity_sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_opportunity_ingestions_source_id", "opportunity_ingestions", ["source_id"])
    op.create_index("ix_opportunity_ingestions_external_id", "opportunity_ingestions", ["external_id"])
    op.create_index(
        "ix_opportunity_ingestions_processing_status",
        "opportunity_ingestions",
        ["processing_status"],
    )
    op.create_index(
        "ix_opportunity_ingestions_opportunity_id",
        "opportunity_ingestions",
        ["opportunity_id"],
    )

    op.create_table(
        "opportunity_sync_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sync_run_status, nullable=False),
        sa.Column("found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("triggered_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["opportunity_sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["triggered_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_opportunity_sync_runs_source_id", "opportunity_sync_runs", ["source_id"])
    op.create_index("ix_opportunity_sync_runs_status", "opportunity_sync_runs", ["status"])

    op.create_table(
        "opportunity_risk_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flag_type", sa.String(length=80), nullable=False),
        sa.Column("severity", risk_severity, nullable=False),
        sa.Column("flag_source", sa.String(length=40), nullable=False, server_default="rule"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_opportunity_risk_flags_opportunity_id",
        "opportunity_risk_flags",
        ["opportunity_id"],
    )
    op.create_index("ix_opportunity_risk_flags_flag_type", "opportunity_risk_flags", ["flag_type"])


def downgrade() -> None:
    op.drop_index("ix_opportunity_risk_flags_flag_type", table_name="opportunity_risk_flags")
    op.drop_index("ix_opportunity_risk_flags_opportunity_id", table_name="opportunity_risk_flags")
    op.drop_table("opportunity_risk_flags")
    op.drop_index("ix_opportunity_sync_runs_status", table_name="opportunity_sync_runs")
    op.drop_index("ix_opportunity_sync_runs_source_id", table_name="opportunity_sync_runs")
    op.drop_table("opportunity_sync_runs")
    op.drop_index("ix_opportunity_ingestions_opportunity_id", table_name="opportunity_ingestions")
    op.drop_index("ix_opportunity_ingestions_processing_status", table_name="opportunity_ingestions")
    op.drop_index("ix_opportunity_ingestions_external_id", table_name="opportunity_ingestions")
    op.drop_index("ix_opportunity_ingestions_source_id", table_name="opportunity_ingestions")
    op.drop_table("opportunity_ingestions")
    op.execute("DROP INDEX IF EXISTS uq_opportunities_source_external")
    op.drop_constraint("fk_opportunities_duplicate_of_id", "opportunities", type_="foreignkey")
    op.drop_index("ix_opportunities_duplicate_of_id", table_name="opportunities")
    op.drop_index("ix_opportunities_external_id", table_name="opportunities")
    op.drop_column("opportunities", "duplicate_of_id")
    op.drop_column("opportunities", "relevance_score")
    op.drop_column("opportunities", "content_hash")
    op.drop_column("opportunities", "external_id")
    op.drop_column("opportunities", "is_manual")
    op.drop_column("opportunity_sources", "last_error")
    op.execute("DROP TYPE IF EXISTS opportunity_risk_flag_severity")
    op.execute("DROP TYPE IF EXISTS opportunity_sync_run_status")
    op.execute("DROP TYPE IF EXISTS opportunity_ingestion_status")
