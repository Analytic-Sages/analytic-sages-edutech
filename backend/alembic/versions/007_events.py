"""Public events and free registrations

Revision ID: 007_events
Revises: 006_self_paced_lms
Create Date: 2026-08-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_events"
down_revision: Union[str, None] = "006_self_paced_lms"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

event_type = postgresql.ENUM(
    "workshop",
    "webinar",
    "masterclass",
    "ama",
    "community",
    "career",
    "other",
    name="event_type",
    create_type=False,
)

event_registration_status = postgresql.ENUM(
    "registered",
    "cancelled",
    name="event_registration_status",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        "CREATE TYPE event_type AS ENUM "
        "('workshop', 'webinar', 'masterclass', 'ama', 'community', 'career', 'other')"
    )
    op.execute("CREATE TYPE event_registration_status AS ENUM ('registered', 'cancelled')")

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("short_description", sa.String(length=400), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("cover_image", sa.String(length=500), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Africa/Lagos"),
        sa.Column("price", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("registration_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("host_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("host_name", sa.String(length=255), nullable=True),
        sa.Column("youtube_live_url", sa.String(length=500), nullable=True),
        sa.Column("recording_url", sa.String(length=500), nullable=True),
        sa.Column("learn_topics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("audience", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("prerequisites", sa.Text(), nullable=False, server_default=""),
        sa.Column("related_course_slug", sa.String(length=160), nullable=True),
        sa.Column("seo_title", sa.String(length=255), nullable=True),
        sa.Column("seo_description", sa.String(length=400), nullable=True),
        sa.Column("published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cancelled", sa.Boolean(), nullable=False, server_default="false"),
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
        sa.ForeignKeyConstraint(["host_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_events_slug", "events", ["slug"])
    op.create_index("ix_events_starts_at", "events", ["starts_at"])
    op.create_index("ix_events_host_user_id", "events", ["host_user_id"])

    op.create_table(
        "event_registrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", event_registration_status, nullable=False),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("join_clicked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=True),
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
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "event_id", name="uq_event_registrations_user_event"),
    )
    op.create_index("ix_event_registrations_user_id", "event_registrations", ["user_id"])
    op.create_index("ix_event_registrations_event_id", "event_registrations", ["event_id"])


def downgrade() -> None:
    op.drop_index("ix_event_registrations_event_id", table_name="event_registrations")
    op.drop_index("ix_event_registrations_user_id", table_name="event_registrations")
    op.drop_table("event_registrations")
    op.drop_index("ix_events_host_user_id", table_name="events")
    op.drop_index("ix_events_starts_at", table_name="events")
    op.drop_index("ix_events_slug", table_name="events")
    op.drop_table("events")
    op.execute("DROP TYPE event_registration_status")
    op.execute("DROP TYPE event_type")
