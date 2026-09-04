"""Tuition billing plans, accounts, obligations, and payment links

Revision ID: 016_tuition_billing
Revises: 015_drop_stripe_provider
Create Date: 2026-09-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "016_tuition_billing"
down_revision: Union[str, None] = "015_drop_stripe_provider"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE tuition_plan_type AS ENUM "
        "('one_time', 'installment', 'monthly', 'custom')"
    )
    op.execute(
        "CREATE TYPE tuition_due_rule AS ENUM "
        "('immediate', 'specific_date', 'week_number', 'before_cohort_start')"
    )
    op.execute(
        "CREATE TYPE billing_status AS ENUM "
        "('pending', 'current', 'past_due', 'grace_period', 'payment_hold', "
        "'paid_in_full', 'cancelled', 'refunded')"
    )
    op.execute(
        "CREATE TYPE obligation_status AS ENUM "
        "('upcoming', 'open', 'processing', 'paid', 'past_due', 'waived', 'cancelled')"
    )

    tuition_plan_type = postgresql.ENUM(
        "one_time",
        "installment",
        "monthly",
        "custom",
        name="tuition_plan_type",
        create_type=False,
    )
    tuition_due_rule = postgresql.ENUM(
        "immediate",
        "specific_date",
        "week_number",
        "before_cohort_start",
        name="tuition_due_rule",
        create_type=False,
    )
    billing_status = postgresql.ENUM(
        "pending",
        "current",
        "past_due",
        "grace_period",
        "payment_hold",
        "paid_in_full",
        "cancelled",
        "refunded",
        name="billing_status",
        create_type=False,
    )
    obligation_status = postgresql.ENUM(
        "upcoming",
        "open",
        "processing",
        "paid",
        "past_due",
        "waived",
        "cancelled",
        name="obligation_status",
        create_type=False,
    )

    op.create_table(
        "tuition_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("plan_type", tuition_plan_type, nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("base_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("number_of_installments", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("available_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("available_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
        sa.ForeignKeyConstraint(["cohort_id"], ["cohorts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tuition_plans_course_id", "tuition_plans", ["course_id"])
    op.create_index("ix_tuition_plans_cohort_id", "tuition_plans", ["cohort_id"])

    op.create_table(
        "tuition_plan_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tuition_plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("due_rule", tuition_due_rule, nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("week_number", sa.Integer(), nullable=True),
        sa.Column("offset_days", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tuition_plan_id"], ["tuition_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tuition_plan_id", "sequence_number", name="uq_tuition_plan_schedule_seq"
        ),
    )
    op.create_index(
        "ix_tuition_plan_schedules_tuition_plan_id",
        "tuition_plan_schedules",
        ["tuition_plan_id"],
    )

    op.create_table(
        "student_billing_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tuition_plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "discount_amount",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "scholarship_amount",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("final_amount_due", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "amount_paid",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("amount_outstanding", sa.Numeric(12, 2), nullable=False),
        sa.Column("billing_status", billing_status, nullable=False),
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
        sa.ForeignKeyConstraint(["cohort_id"], ["cohorts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tuition_plan_id"], ["tuition_plans.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_student_billing_accounts_student_id", "student_billing_accounts", ["student_id"]
    )
    op.create_index(
        "ix_student_billing_accounts_course_id", "student_billing_accounts", ["course_id"]
    )
    op.create_index(
        "ix_student_billing_accounts_cohort_id", "student_billing_accounts", ["cohort_id"]
    )
    op.create_index(
        "ix_student_billing_accounts_tuition_plan_id",
        "student_billing_accounts",
        ["tuition_plan_id"],
    )

    op.create_table(
        "payment_obligations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("billing_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("amount_due", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", obligation_status, nullable=False),
        sa.Column(
            "paid_amount",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
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
            ["billing_account_id"], ["student_billing_accounts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "billing_account_id", "sequence_number", name="uq_obligation_account_seq"
        ),
    )
    op.create_index(
        "ix_payment_obligations_billing_account_id",
        "payment_obligations",
        ["billing_account_id"],
    )

    op.create_table(
        "billing_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("before_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_billing_audit_events_actor_id", "billing_audit_events", ["actor_id"])
    op.create_index("ix_billing_audit_events_entity_id", "billing_audit_events", ["entity_id"])

    op.add_column(
        "payments",
        sa.Column("billing_account_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("payment_obligation_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_payments_billing_account_id", "payments", ["billing_account_id"])
    op.create_index(
        "ix_payments_payment_obligation_id", "payments", ["payment_obligation_id"]
    )
    op.create_foreign_key(
        "fk_payments_billing_account_id",
        "payments",
        "student_billing_accounts",
        ["billing_account_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_payments_payment_obligation_id",
        "payments",
        "payment_obligations",
        ["payment_obligation_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "payment_webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("event_key", sa.String(length=255), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "event_key", name="uq_payment_webhook_provider_event"),
    )
    op.create_index("ix_payment_webhook_events_provider", "payment_webhook_events", ["provider"])
    op.create_index(
        "ix_payment_webhook_events_payment_id", "payment_webhook_events", ["payment_id"]
    )


def downgrade() -> None:
    op.drop_table("payment_webhook_events")
    op.drop_constraint("fk_payments_payment_obligation_id", "payments", type_="foreignkey")
    op.drop_constraint("fk_payments_billing_account_id", "payments", type_="foreignkey")
    op.drop_index("ix_payments_payment_obligation_id", table_name="payments")
    op.drop_index("ix_payments_billing_account_id", table_name="payments")
    op.drop_column("payments", "payment_obligation_id")
    op.drop_column("payments", "billing_account_id")
    op.drop_table("billing_audit_events")
    op.drop_table("payment_obligations")
    op.drop_table("student_billing_accounts")
    op.drop_table("tuition_plan_schedules")
    op.drop_table("tuition_plans")
    op.execute("DROP TYPE obligation_status")
    op.execute("DROP TYPE billing_status")
    op.execute("DROP TYPE tuition_due_rule")
    op.execute("DROP TYPE tuition_plan_type")
