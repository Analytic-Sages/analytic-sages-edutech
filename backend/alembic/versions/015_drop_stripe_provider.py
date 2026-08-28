"""Drop unused Stripe payment provider

Revision ID: 015_drop_stripe_provider
Revises: 014_opportunity_engagement
Create Date: 2026-08-28
"""

from typing import Sequence, Union

from alembic import op

revision: str = "015_drop_stripe_provider"
down_revision: Union[str, None] = "014_opportunity_engagement"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM payments WHERE provider::text = 'stripe'")
    op.execute("ALTER TYPE payment_provider RENAME TO payment_provider_old")
    op.execute("CREATE TYPE payment_provider AS ENUM ('mock', 'paystack', 'nowpayments')")
    op.execute(
        "ALTER TABLE payments ALTER COLUMN provider TYPE payment_provider "
        "USING provider::text::payment_provider"
    )
    op.execute("DROP TYPE payment_provider_old")


def downgrade() -> None:
    op.execute("ALTER TYPE payment_provider RENAME TO payment_provider_old")
    op.execute(
        "CREATE TYPE payment_provider AS ENUM ('mock', 'stripe', 'paystack', 'nowpayments')"
    )
    op.execute(
        "ALTER TABLE payments ALTER COLUMN provider TYPE payment_provider "
        "USING provider::text::payment_provider"
    )
    op.execute("DROP TYPE payment_provider_old")
