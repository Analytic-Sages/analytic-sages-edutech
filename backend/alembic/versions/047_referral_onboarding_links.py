"""Referral partner applications, cohorts, onboarding and multi-course links.

Revision ID: 047_referral_onboarding_links
Revises: 046_course_card_placements
Create Date: 2026-10-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "047_referral_onboarding_links"
down_revision: Union[str, None] = "046_course_card_placements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


APPLICATION_STATUSES = (
    "submitted",
    "under_review",
    "shortlisted",
    "interviewed",
    "approved",
    "onboarding",
    "active",
    "rejected",
    "waitlisted",
    "suspended",
    "inactive",
)


def upgrade() -> None:
    op.create_table(
        "referral_partner_cohorts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("capacity > 0", name="ck_referral_partner_cohorts_capacity_positive"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_referral_partner_cohorts_active", "referral_partner_cohorts", ["is_active"])

    op.create_table(
        "referral_partner_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("email_normalized", sa.String(320), nullable=False),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("timezone", sa.String(100), nullable=True),
        sa.Column("linkedin_url", sa.String(512), nullable=True),
        sa.Column("social_profiles", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("communities", sa.Text(), nullable=True),
        sa.Column("audience_size", sa.String(80), nullable=True),
        sa.Column("audience_engagement", sa.Text(), nullable=True),
        sa.Column("relevant_experience", sa.Text(), nullable=True),
        sa.Column("partnership_experience", sa.Text(), nullable=True),
        sa.Column("interested_courses", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("promotion_channels", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("marketing_plan", sa.Text(), nullable=False),
        sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("terms_version", sa.String(40), nullable=False, server_default="referral-partner-v1"),
        sa.Column("marketing_guidelines_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="submitted"),
        sa.Column("scores", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("score_total", sa.Integer(), nullable=True),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("interview_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("interview_status", sa.String(32), nullable=True),
        sa.Column("interview_reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("interview_notes", sa.Text(), nullable=True),
        sa.Column("interview_decision", sa.String(32), nullable=True),
        sa.Column("interview_reason", sa.Text(), nullable=True),
        sa.Column("follow_up_actions", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "status IN ('submitted','under_review','shortlisted','interviewed','approved','onboarding','active','rejected','waitlisted','suspended','inactive')",
            name="ck_referral_partner_applications_status",
        ),
        sa.CheckConstraint("score_total IS NULL OR (score_total >= 0 AND score_total <= 100)", name="ck_referral_partner_applications_score"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["partner_id"], ["referral_partners.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cohort_id"], ["referral_partner_cohorts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["interview_reviewer_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("uq_referral_partner_applications_email", "referral_partner_applications", ["email_normalized"], unique=True)
    op.create_index("ix_referral_partner_applications_status", "referral_partner_applications", ["status"])
    op.create_index("ix_referral_partner_applications_cohort", "referral_partner_applications", ["cohort_id"])
    op.create_index("ix_referral_partner_applications_created", "referral_partner_applications", ["created_at"])

    op.create_table(
        "referral_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_type", sa.String(16), nullable=False, server_default="general"),
        sa.Column("target_slug", sa.String(160), nullable=True),
        sa.Column("campaign_label", sa.String(120), nullable=True),
        sa.Column("campaign_channel", sa.String(80), nullable=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("destination_path", sa.String(512), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="inactive"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["partner_id"], ["referral_partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cohort_id"], ["cohorts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["revoked_by"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint("status IN ('inactive','active','revoked')", name="ck_referral_links_status"),
        sa.CheckConstraint("course_id IS NULL OR cohort_id IS NULL", name="ck_referral_links_one_target"),
        sa.CheckConstraint("target_type IN ('general','course','programme')", name="ck_referral_links_target_type"),
    )
    op.create_index("ix_referral_links_partner", "referral_links", ["partner_id"])
    op.create_index("ix_referral_links_course", "referral_links", ["course_id"])
    op.create_index("ix_referral_links_cohort", "referral_links", ["cohort_id"])
    op.create_index("ix_referral_links_status", "referral_links", ["status"])

    op.add_column("referral_partners", sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("referral_partners", sa.Column("profile_completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("referral_partners", sa.Column("marketing_guidelines_accepted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("referral_partners", sa.Column("onboarding_terms_version", sa.String(40), nullable=True))
    op.add_column("referral_partners", sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_referral_partners_cohort_id",
        "referral_partners",
        "referral_partner_cohorts",
        ["cohort_id"],
        ["id"],
        ondelete="SET NULL",
    )

    for table in ("referral_clicks", "referral_attributions", "referral_conversions"):
        op.add_column(table, sa.Column("referral_link_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            f"fk_{table}_referral_link_id",
            table,
            "referral_links",
            ["referral_link_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(f"ix_{table}_referral_link_id", table, ["referral_link_id"])

    op.create_table(
        "referral_program_resources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("terms_version", sa.String(40), nullable=False),
        sa.Column("program_overview", sa.Text(), nullable=False),
        sa.Column("commission_policy", sa.Text(), nullable=False),
        sa.Column("attribution_policy", sa.Text(), nullable=False),
        sa.Column("payout_policy", sa.Text(), nullable=False),
        sa.Column("marketing_guidelines", sa.Text(), nullable=False),
        sa.Column("support_contact", sa.String(320), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_referral_program_resources_singleton"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.execute(
        """
        INSERT INTO referral_program_resources
            (id, terms_version, program_overview, commission_policy, attribution_policy, payout_policy, marketing_guidelines, support_contact)
        VALUES
            (1, 'referral-partner-v1',
             'The Referral Partner Programme helps learners discover eligible paid Analytic Sages courses and programmes through trusted recommendations.',
             'Standard commission is 7% of each eligible, confirmed payment, including eligible installments. Commissions are payment-level and idempotent. Refunds, reversals, fraud review and eligibility rules apply. A 14-day hold applies before funds become available.',
             'Attribution lasts 30 days. The existing first-valid-referral and account-locking rules apply. A link may point to one course while the learner purchases another eligible course within the attribution window, subject to the established attribution policy.',
             'Payout requests are reviewed and approved manually by an administrator. Existing currency-specific minimums apply. Balances remain in their original transaction currencies; USD figures are estimates for reporting only. A commission is not payable until it is eligible and available.',
             'Be transparent that you are sharing a referral link. Do not spam, impersonate Analytic Sages, make unsupported earnings or employment claims, promise discounts or scholarships without written approval, or misrepresent course content. Respect platform rules, privacy and consent. Use only approved brand assets and current course information.',
             'support@analyticsages.io')
        ON CONFLICT (id) DO NOTHING
        """
    )

    # Cohort 1 is the initial, configurable ten-person cohort. A fixed ID keeps
    # this seed deterministic across deployments without requiring an extension.
    op.execute(
        """
        INSERT INTO referral_partner_cohorts (id, name, capacity, is_active)
        VALUES ('00000000-0000-0000-0000-000000000047', 'Cohort 1', 10, true)
        ON CONFLICT (name) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("referral_program_resources")
    for table in ("referral_conversions", "referral_attributions", "referral_clicks"):
        op.drop_index(f"ix_{table}_referral_link_id", table_name=table)
        op.drop_constraint(f"fk_{table}_referral_link_id", table, type_="foreignkey")
        op.drop_column(table, "referral_link_id")

    op.drop_constraint("fk_referral_partners_cohort_id", "referral_partners", type_="foreignkey")
    op.drop_column("referral_partners", "onboarding_completed_at")
    op.drop_column("referral_partners", "onboarding_terms_version")
    op.drop_column("referral_partners", "marketing_guidelines_accepted_at")
    op.drop_column("referral_partners", "profile_completed_at")
    op.drop_column("referral_partners", "cohort_id")

    op.drop_table("referral_links")
    op.drop_index("ix_referral_partner_applications_created", table_name="referral_partner_applications")
    op.drop_index("ix_referral_partner_applications_cohort", table_name="referral_partner_applications")
    op.drop_index("ix_referral_partner_applications_status", table_name="referral_partner_applications")
    op.drop_index("uq_referral_partner_applications_email", table_name="referral_partner_applications")
    op.drop_table("referral_partner_applications")
    op.drop_index("ix_referral_partner_cohorts_active", table_name="referral_partner_cohorts")
    op.drop_table("referral_partner_cohorts")
