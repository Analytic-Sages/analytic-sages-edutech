"""Opportunities hub: taxonomy, sources, listings, and verification audit

Revision ID: 012_opportunities
Revises: 011_insight_newsletter
Create Date: 2026-08-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012_opportunities"
down_revision: Union[str, None] = "011_insight_newsletter"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE opportunity_type AS ENUM "
        "('job', 'internship', 'fellowship', 'hackathon', 'grant', 'bounty', 'research', 'other')"
    )
    op.execute(
        "CREATE TYPE employment_type AS ENUM "
        "('full_time', 'part_time', 'contract', 'internship', 'volunteer', 'other')"
    )
    op.execute(
        "CREATE TYPE experience_level AS ENUM "
        "('intern', 'junior', 'mid', 'senior', 'lead', 'not_specified')"
    )
    op.execute("CREATE TYPE workplace_type AS ENUM ('remote', 'hybrid', 'onsite')")
    op.execute(
        "CREATE TYPE opportunity_status AS ENUM "
        "('draft', 'published', 'rejected', 'expired', 'archived')"
    )
    op.execute(
        "CREATE TYPE opportunity_trust_status AS ENUM "
        "('unverified', 'high_confidence', 'source_checked', 'review_required', 'high_risk')"
    )
    op.execute(
        "CREATE TYPE opportunity_public_badge AS ENUM "
        "('none', 'official_source', 'partner', 'source_checked', 'community_submission')"
    )
    op.execute(
        "CREATE TYPE opportunity_source_type AS ENUM "
        "('official_company', 'partner', 'job_board', 'hackathon_platform', 'community', 'manual', 'api', 'rss')"
    )
    op.execute("CREATE TYPE opportunity_source_trust_level AS ENUM ('high', 'medium', 'low')")
    op.execute("CREATE TYPE opportunity_source_health AS ENUM ('unknown', 'healthy', 'degraded', 'down')")
    op.execute("CREATE TYPE opportunity_skill_importance AS ENUM ('low', 'medium', 'high')")
    op.execute(
        "CREATE TYPE verification_event_type AS ENUM "
        "('created', 'updated', 'admin_approval', 'admin_reject', 'admin_archive', 'admin_unpublish')"
    )
    op.execute(
        "CREATE TYPE verification_event_result AS ENUM "
        "('recorded', 'approved', 'rejected', 'archived', 'unpublished')"
    )

    opportunity_type = postgresql.ENUM(
        "job",
        "internship",
        "fellowship",
        "hackathon",
        "grant",
        "bounty",
        "research",
        "other",
        name="opportunity_type",
        create_type=False,
    )
    employment_type = postgresql.ENUM(
        "full_time",
        "part_time",
        "contract",
        "internship",
        "volunteer",
        "other",
        name="employment_type",
        create_type=False,
    )
    experience_level = postgresql.ENUM(
        "intern",
        "junior",
        "mid",
        "senior",
        "lead",
        "not_specified",
        name="experience_level",
        create_type=False,
    )
    workplace_type = postgresql.ENUM(
        "remote",
        "hybrid",
        "onsite",
        name="workplace_type",
        create_type=False,
    )
    opportunity_status = postgresql.ENUM(
        "draft",
        "published",
        "rejected",
        "expired",
        "archived",
        name="opportunity_status",
        create_type=False,
    )
    opportunity_trust_status = postgresql.ENUM(
        "unverified",
        "high_confidence",
        "source_checked",
        "review_required",
        "high_risk",
        name="opportunity_trust_status",
        create_type=False,
    )
    opportunity_public_badge = postgresql.ENUM(
        "none",
        "official_source",
        "partner",
        "source_checked",
        "community_submission",
        name="opportunity_public_badge",
        create_type=False,
    )
    opportunity_source_type = postgresql.ENUM(
        "official_company",
        "partner",
        "job_board",
        "hackathon_platform",
        "community",
        "manual",
        "api",
        "rss",
        name="opportunity_source_type",
        create_type=False,
    )
    opportunity_source_trust_level = postgresql.ENUM(
        "high",
        "medium",
        "low",
        name="opportunity_source_trust_level",
        create_type=False,
    )
    opportunity_source_health = postgresql.ENUM(
        "unknown",
        "healthy",
        "degraded",
        "down",
        name="opportunity_source_health",
        create_type=False,
    )
    opportunity_skill_importance = postgresql.ENUM(
        "low",
        "medium",
        "high",
        name="opportunity_skill_importance",
        create_type=False,
    )
    verification_event_type = postgresql.ENUM(
        "created",
        "updated",
        "admin_approval",
        "admin_reject",
        "admin_archive",
        "admin_unpublish",
        name="verification_event_type",
        create_type=False,
    )
    verification_event_result = postgresql.ENUM(
        "recorded",
        "approved",
        "rejected",
        "archived",
        "unpublished",
        name="verification_event_result",
        create_type=False,
    )

    op.create_table(
        "career_paths",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_career_paths_slug", "career_paths", ["slug"], unique=True)

    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False, server_default="general"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_skills_slug", "skills", ["slug"], unique=True)

    op.create_table(
        "opportunity_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("source_type", opportunity_source_type, nullable=False),
        sa.Column("trust_level", opportunity_source_trust_level, nullable=False),
        sa.Column("automation_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("auto_publish_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("connector_type", sa.String(length=80), nullable=False, server_default="manual"),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("health_status", opportunity_source_health, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("organization_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("requirements", sa.Text(), nullable=False, server_default=""),
        sa.Column("responsibilities", sa.Text(), nullable=True),
        sa.Column("benefits", sa.Text(), nullable=True),
        sa.Column("opportunity_type", opportunity_type, nullable=False),
        sa.Column("employment_type", employment_type, nullable=True),
        sa.Column("experience_level", experience_level, nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("workplace_type", workplace_type, nullable=False),
        sa.Column("application_url", sa.String(length=500), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", opportunity_status, nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("trust_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("trust_status", opportunity_trust_status, nullable=False),
        sa.Column("public_badge", opportunity_public_badge, nullable=False),
        sa.Column("featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("admin_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["opportunity_sources.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_opportunities_slug", "opportunities", ["slug"], unique=True)
    op.create_index("ix_opportunities_opportunity_type", "opportunities", ["opportunity_type"])
    op.create_index("ix_opportunities_status", "opportunities", ["status"])
    op.create_index("ix_opportunities_deadline", "opportunities", ["deadline"])
    op.create_index("ix_opportunities_source_id", "opportunities", ["source_id"])
    op.create_index("ix_opportunities_created_by", "opportunities", ["created_by"])
    op.create_index(
        "ix_opportunities_status_published_at",
        "opportunities",
        ["status", "published_at"],
    )

    op.create_table(
        "opportunity_career_paths",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("career_path_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relevance_score", sa.Numeric(4, 3), nullable=False, server_default="1.000"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["career_path_id"], ["career_paths.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("opportunity_id", "career_path_id", name="uq_opportunity_career_paths"),
    )
    op.create_index("ix_opportunity_career_paths_opportunity_id", "opportunity_career_paths", ["opportunity_id"])
    op.create_index("ix_opportunity_career_paths_career_path_id", "opportunity_career_paths", ["career_path_id"])

    op.create_table(
        "opportunity_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("importance", opportunity_skill_importance, nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("opportunity_id", "skill_id", name="uq_opportunity_skills"),
    )
    op.create_index("ix_opportunity_skills_opportunity_id", "opportunity_skills", ["opportunity_id"])
    op.create_index("ix_opportunity_skills_skill_id", "opportunity_skills", ["skill_id"])

    op.create_table(
        "verification_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", verification_event_type, nullable=False),
        sa.Column("result", verification_event_result, nullable=False),
        sa.Column("performed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["performed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verification_events_opportunity_id", "verification_events", ["opportunity_id"])


def downgrade() -> None:
    op.drop_index("ix_verification_events_opportunity_id", table_name="verification_events")
    op.drop_table("verification_events")
    op.drop_index("ix_opportunity_skills_skill_id", table_name="opportunity_skills")
    op.drop_index("ix_opportunity_skills_opportunity_id", table_name="opportunity_skills")
    op.drop_table("opportunity_skills")
    op.drop_index("ix_opportunity_career_paths_career_path_id", table_name="opportunity_career_paths")
    op.drop_index("ix_opportunity_career_paths_opportunity_id", table_name="opportunity_career_paths")
    op.drop_table("opportunity_career_paths")
    op.drop_index("ix_opportunities_status_published_at", table_name="opportunities")
    op.drop_index("ix_opportunities_created_by", table_name="opportunities")
    op.drop_index("ix_opportunities_source_id", table_name="opportunities")
    op.drop_index("ix_opportunities_deadline", table_name="opportunities")
    op.drop_index("ix_opportunities_status", table_name="opportunities")
    op.drop_index("ix_opportunities_opportunity_type", table_name="opportunities")
    op.drop_index("ix_opportunities_slug", table_name="opportunities")
    op.drop_table("opportunities")
    op.drop_table("opportunity_sources")
    op.drop_index("ix_skills_slug", table_name="skills")
    op.drop_table("skills")
    op.drop_index("ix_career_paths_slug", table_name="career_paths")
    op.drop_table("career_paths")
    op.execute("DROP TYPE IF EXISTS verification_event_result")
    op.execute("DROP TYPE IF EXISTS verification_event_type")
    op.execute("DROP TYPE IF EXISTS opportunity_skill_importance")
    op.execute("DROP TYPE IF EXISTS opportunity_source_health")
    op.execute("DROP TYPE IF EXISTS opportunity_source_trust_level")
    op.execute("DROP TYPE IF EXISTS opportunity_source_type")
    op.execute("DROP TYPE IF EXISTS opportunity_public_badge")
    op.execute("DROP TYPE IF EXISTS opportunity_trust_status")
    op.execute("DROP TYPE IF EXISTS opportunity_status")
    op.execute("DROP TYPE IF EXISTS workplace_type")
    op.execute("DROP TYPE IF EXISTS experience_level")
    op.execute("DROP TYPE IF EXISTS employment_type")
    op.execute("DROP TYPE IF EXISTS opportunity_type")
