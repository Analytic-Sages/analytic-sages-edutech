"""Add WhatsApp and Telegram contact fields to partner applications.

Revision ID: 048_ref_partner_contacts
Revises: 047_referral_onboarding_links
Create Date: 2026-10-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "048_ref_partner_contacts"
down_revision: Union[str, None] = "047_referral_onboarding_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable for legacy applications; new application requests require both.
    op.add_column("referral_partner_applications", sa.Column("whatsapp_number", sa.String(40), nullable=True))
    op.add_column("referral_partner_applications", sa.Column("telegram_id", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("referral_partner_applications", "telegram_id")
    op.drop_column("referral_partner_applications", "whatsapp_number")
