"""Update SQL & Excel Cohort 1 deadline and timetable for November 9 start.

Revision ID: 051_sql_excel_nov_dates
Revises: 050_sql_excel_reopen
Create Date: 2026-10-20
"""

from typing import Sequence, Union

from alembic import op

revision: str = "051_sql_excel_nov_dates"
down_revision: Union[str, Sequence[str], None] = "050_sql_excel_reopen"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Registration closes at 23:59:59 Africa/Lagos on November 7 (22:59:59 UTC).
    op.execute(
        """
        UPDATE cohorts
        SET
            registration_deadline = TIMESTAMPTZ '2026-11-07 22:59:59+00',
            starts_at = TIMESTAMPTZ '2026-11-09 00:00:00+00',
            ends_at = TIMESTAMPTZ '2026-12-18 23:59:59+00',
            status = 'open',
            updated_at = now()
        WHERE slug = 'cohort-9-blockchain-data'
        """
    )

    # Move active scheduled sessions forward one week to match the revised
    # November 9–December 18 six-week curriculum.
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
          AND s.status = 'scheduled'
          AND s.starts_at >= TIMESTAMPTZ '2026-11-02 00:00:00+00'
          AND s.starts_at < TIMESTAMPTZ '2026-12-12 00:00:00+00'
        """
    )


def downgrade() -> None:
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
          AND s.status = 'scheduled'
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
            status = 'open',
            updated_at = now()
        WHERE slug = 'cohort-9-blockchain-data'
        """
    )
