"""Reopen SQL & Excel Cohort 1 registration through October 31.

Revision ID: 050_sql_excel_reopen
Revises: 049_sql_excel_dates
Create Date: 2026-10-20
"""

from typing import Sequence, Union

from alembic import op

revision: str = "050_sql_excel_reopen"
down_revision: Union[str, Sequence[str], None] = "049_sql_excel_dates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep the cohort open through the end of October in Africa/Lagos (UTC+1),
    # with classes beginning November 2 as originally scheduled.
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

    # Migration 049 shifted this cohort's scheduled sessions one week later.
    # Restore the November 2–December 11 timetable without touching cancelled
    # or archived sessions.
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


def downgrade() -> None:
    # Revert the session shift and cohort metadata to the values set by
    # migration 049_sql_excel_dates.
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
    op.execute(
        """
        UPDATE cohorts
        SET
            registration_deadline = TIMESTAMPTZ '2026-10-07 22:59:59+00',
            starts_at = TIMESTAMPTZ '2026-11-09 00:00:00+00',
            ends_at = TIMESTAMPTZ '2026-12-18 23:59:59+00',
            status = 'open',
            updated_at = now()
        WHERE slug = 'cohort-9-blockchain-data'
        """
    )
