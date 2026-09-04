"""Referral Partner Program tables

Revision ID: 021_referral_partner_program
Revises: 020_partnerships_role
Create Date: 2026-09-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "021_referral_partner_program"
down_revision: Union[str, None] = "020_partnerships_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE referral_partner_status AS ENUM "
        "('pending', 'active', 'suspended', 'rejected')"
    )
    op.execute(
        "CREATE TYPE referral_conversion_status AS ENUM "
        "('pending', 'available', 'voided', 'reversed', 'review_required')"
    )
    op.execute(
        "CREATE TYPE partner_ledger_entry_type AS ENUM "
        "('commission', 'reversal', 'payout', 'adjustment')"
    )
    op.execute(
        "CREATE TYPE partner_ledger_status AS ENUM "
        "('pending', 'available', 'reserved', 'processing', 'completed', 'voided')"
    )
    op.execute(
        "CREATE TYPE partner_payout_status AS ENUM "
        "('requested', 'approved', 'processing', 'paid', 'rejected', 'cancelled')"
    )

    partner_status = postgresql.ENUM(
        "pending", "active", "suspended", "rejected",
        name="referral_partner_status", create_type=False,
    )
    conversion_status = postgresql.ENUM(
        "pending", "available", "voided", "reversed", "review_required",
        name="referral_conversion_status", create_type=False,
    )
    ledger_type = postgresql.ENUM(
        "commission", "reversal", "payout", "adjustment",
        name="partner_ledger_entry_type", create_type=False,
    )
    ledger_status = postgresql.ENUM(
        "pending", "available", "reserved", "processing", "completed", "voided",
        name="partner_ledger_status", create_type=False,
    )
    payout_status = postgresql.ENUM(
        "requested", "approved", "processing", "paid", "rejected", "cancelled",
        name="partner_payout_status", create_type=False,
    )

    op.add_column(
        "courses",
        sa.Column(
            "referral_commission_eligible",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "cohorts",
        sa.Column(
            "referral_commission_eligible",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    op.create_table(
        "referral_partners",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", partner_status, nullable=False, server_default="pending"),
        sa.Column("referral_code", sa.String(32), nullable=True),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("social_handle", sa.String(160), nullable=True),
        sa.Column("promotion_channels", sa.Text(), nullable=True),
        sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("referral_code"),
    )
    op.create_index("ix_referral_partners_status", "referral_partners", ["status"])
    op.create_index("ix_referral_partners_referral_code", "referral_partners", ["referral_code"])

    op.create_table(
        "referral_clicks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("referral_code", sa.String(32), nullable=False),
        sa.Column("anonymous_visitor_id", sa.String(64), nullable=False),
        sa.Column("landing_path", sa.String(512), nullable=True),
        sa.Column("ip_hash", sa.String(64), nullable=True),
        sa.Column("user_agent_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["referral_partners.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_referral_clicks_partner_id", "referral_clicks", ["partner_id"])
    op.create_index("ix_referral_clicks_code", "referral_clicks", ["referral_code"])
    op.create_index("ix_referral_clicks_visitor", "referral_clicks", ["anonymous_visitor_id"])
    op.create_index("ix_referral_clicks_created", "referral_clicks", ["created_at"])

    op.create_table(
        "referral_attributions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("anonymous_visitor_id", sa.String(64), nullable=False),
        sa.Column("referred_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("referral_code", sa.String(32), nullable=False),
        sa.Column("landing_path", sa.String(512), nullable=True),
        sa.Column("attributed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["referral_partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["referred_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_referral_attr_partner", "referral_attributions", ["partner_id"])
    op.create_index("ix_referral_attr_visitor", "referral_attributions", ["anonymous_visitor_id"])
    op.create_index("ix_referral_attr_user", "referral_attributions", ["referred_user_id"])
    op.create_index("ix_referral_attr_expires", "referral_attributions", ["expires_at"])
    op.execute(
        "CREATE UNIQUE INDEX uq_referral_attr_locked_user "
        "ON referral_attributions (referred_user_id) "
        "WHERE locked_at IS NOT NULL AND referred_user_id IS NOT NULL"
    )

    op.create_table(
        "referral_conversions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("referred_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("enrollment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_obligation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("eligible_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("commission_rate", sa.Numeric(8, 6), nullable=False),
        sa.Column("commission_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", conversion_status, nullable=False, server_default="pending"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fraud_flags", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["referral_partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["referred_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cohort_id"], ["cohorts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["payment_obligation_id"], ["payment_obligations.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("payment_id", name="uq_referral_conversions_payment_id"),
    )
    op.create_index("ix_referral_conversions_partner", "referral_conversions", ["partner_id"])
    op.create_index("ix_referral_conversions_user", "referral_conversions", ["referred_user_id"])
    op.create_index("ix_referral_conversions_status", "referral_conversions", ["status"])

    op.create_table(
        "partner_ledger_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entry_type", ledger_type, nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("reference_type", sa.String(64), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", ledger_status, nullable=False, server_default="pending"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["referral_partners.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "partner_id",
            "entry_type",
            "reference_type",
            "reference_id",
            name="uq_partner_ledger_ref",
        ),
    )
    op.create_index("ix_partner_ledger_partner", "partner_ledger_entries", ["partner_id"])
    op.create_index("ix_partner_ledger_status", "partner_ledger_entries", ["status"])
    op.create_index("ix_partner_ledger_ref_id", "partner_ledger_entries", ["reference_id"])

    op.create_table(
        "partner_payout_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("payment_method", sa.String(64), nullable=False, server_default="manual"),
        sa.Column("payment_details_reference", sa.String(255), nullable=True),
        sa.Column("status", payout_status, nullable=False, server_default="requested"),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["referral_partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["processed_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_partner_payouts_partner", "partner_payout_requests", ["partner_id"])
    op.create_index("ix_partner_payouts_status", "partner_payout_requests", ["status"])

    op.create_table(
        "referral_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("before_json", postgresql.JSONB(), nullable=True),
        sa.Column("after_json", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_referral_audit_action", "referral_audit_events", ["action"])
    op.create_index("ix_referral_audit_entity", "referral_audit_events", ["entity_id"])
    op.create_index("ix_referral_audit_created", "referral_audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("referral_audit_events")
    op.drop_table("partner_payout_requests")
    op.drop_table("partner_ledger_entries")
    op.drop_table("referral_conversions")
    op.execute("DROP INDEX IF EXISTS uq_referral_attr_locked_user")
    op.drop_table("referral_attributions")
    op.drop_table("referral_clicks")
    op.drop_table("referral_partners")
    op.drop_column("cohorts", "referral_commission_eligible")
    op.drop_column("courses", "referral_commission_eligible")
    op.execute("DROP TYPE IF EXISTS partner_payout_status")
    op.execute("DROP TYPE IF EXISTS partner_ledger_status")
    op.execute("DROP TYPE IF EXISTS partner_ledger_entry_type")
    op.execute("DROP TYPE IF EXISTS referral_conversion_status")
    op.execute("DROP TYPE IF EXISTS referral_partner_status")
