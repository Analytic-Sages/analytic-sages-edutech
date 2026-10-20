"""Move SQL & Excel Cohort 1 to the updated November 9 launch date.

Revision ID: 048_sql_excel_cohort_dates
Revises: 047_referral_onboarding_links
Create Date: 2026-10-20
"""

from typing import Sequence, Union

from alembic import op

revision: str = "048_sql_excel_cohort_dates"
down_revision: Union[str, Sequence[str], None] = "047_referral_onboarding_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep the database cohort dates in sync with the public programme page.
    op.execute(
        """
        UPDATE cohorts
        SET
            registration_deadline = TIMESTAMPTZ '2026-10-07 22:59:59+00',
            starts_at = TIMESTAMPTZ '2026-11-09 00:00:00+00',
            ends_at = TIMESTAMPTZ '2026-12-18 23:59:59+00',
            updated_at = now()
        WHERE slug = 'cohort-9-blockchain-data'
        """
    )

    # Migration 045 created the canonical timetable one week too early.
    # Shift only those known seed timetable rows; preserve their IDs, attendance,
    # assignments, recordings, session numbers, and status.
    op.execute(
        """
        UPDATE live_sessions AS s
        SET
            starts_at = s.starts_at + INTERVAL '7 days',
            ends_at = s.ends_at + INTERVAL '7 days',
            updated_at = now()
        FROM cohorts AS c
        WHERE s.cohort_id = c.id
          AND c.slug = 'cohort-9-blockchain-data'
          AND s.description = 'SQL & Excel Cohort 1 scheduled session'
          AND s.starts_at >= TIMESTAMPTZ '2026-11-02 00:00:00+00'
          AND s.starts_at < TIMESTAMPTZ '2026-12-12 00:00:00+00'
        """
    )


def downgrade() -> None:
    # Restore the prior timetable dates if this migration is explicitly rolled back.
    op.execute(
        """
        UPDATE live_sessions AS s
        SET
            starts_at = s.starts_at - INTERVAL '7 days',
            ends_at = s.ends_at - INTERVAL '7 days',
            updated_at = now()
        FROM cohorts AS c
        WHERE s.cohort_id = c.id
          AND c.slug = 'cohort-9-blockchain-data'
          AND s.description = 'SQL & Excel Cohort 1 scheduled session'
          AND s.starts_at >= TIMESTAMPTZ '2026-11-09 00:00:00+00'
          AND s.starts_at < TIMESTAMPTZ '2026-12-19 00:00:00+00'
        """
    )
    op.execute(
        """
        UPDATE cohorts
        SET
            registration_deadline = TIMESTAMPTZ '2026-10-31 22:59:59+00',
            starts_at = TIMESTAMPTZ '2026-11-02 00:00:00+00',
            ends_at = TIMESTAMPTZ '2026-12-11 23:59:59+00',
            updated_at = now()
        WHERE slug = 'cohort-9-blockchain-data'
        """
    )
