"""Refresh the SQL & Excel cohort's live checkout metadata.

Revision ID: 044_sql_excel_cohort_launch
Revises: 043_assignment_social_posts
Create Date: 2026-10-15
"""

from typing import Sequence, Union

from alembic import op

revision: str = "044_sql_excel_cohort_launch"
down_revision: Union[str, Sequence[str], None] = "043_assignment_social_posts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The checkout page reads this live row. Updating only the marketing page
    # would leave payment creation using the stale cohort price and dates.
    op.execute(
        """
        UPDATE cohorts
        SET
            name = 'Cohort 1 - SQL & Excel for Blockchain Data Analytics and Research',
            description = 'Onchain Analytics and Research',
            status = 'open',
            registration_deadline = TIMESTAMPTZ '2026-10-31 23:59:59+00',
            starts_at = TIMESTAMPTZ '2026-11-02 00:00:00+00',
            ends_at = TIMESTAMPTZ '2026-12-11 23:59:59+00',
            price = 50,
            currency = 'USD',
            updated_at = now()
        WHERE slug = 'cohort-9-blockchain-data'
        """
    )


def downgrade() -> None:
    # Restore the previous checkout metadata if this data migration is reverted.
    op.execute(
        """
        UPDATE cohorts
        SET
            name = 'Cohort 9 - SQL Blockchain Data Analytics',
            description = 'Onchain Analytics and Research',
            status = 'open',
            registration_deadline = TIMESTAMPTZ '2026-09-30 23:59:59+00',
            starts_at = TIMESTAMPTZ '2026-10-01 00:00:00+00',
            price = 35,
            currency = 'USD',
            updated_at = now()
        WHERE slug = 'cohort-9-blockchain-data'
        """
    )
