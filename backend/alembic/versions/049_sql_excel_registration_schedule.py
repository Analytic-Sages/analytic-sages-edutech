"""Update SQL & Excel registration deadline and shift the six-week timetable.

Revision ID: 049_sql_excel_registration_schedule
Revises: 048_referral_partner_contact_fields
Create Date: 2026-10-20
"""

from typing import Sequence, Union

from alembic import op

revision: str = "049_sql_excel_registration_schedule"
down_revision: Union[str, Sequence[str], None] = "048_referral_partner_contact_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The deadline is end-of-day in Africa/Lagos (UTC+1). Registration has
    # therefore closed; the public course page directs learners to the waitlist.
    op.execute(
        """
        UPDATE cohorts
        SET
            registration_deadline = TIMESTAMPTZ '2026-10-07 22:59:59+00',
            starts_at = TIMESTAMPTZ '2026-11-09 00:00:00+00',
            ends_at = TIMESTAMPTZ '2026-12-18 23:59:59+00',
            status = 'closed',
            updated_at = now()
        WHERE slug = 'cohort-9-blockchain-data'
        """
    )

    # Shift only the active scheduled SQL & Excel sessions created for the
    # launch timetable. Cancelled/archived legacy sessions and learner records
    # remain untouched.
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
            registration_deadline = TIMESTAMPTZ '2026-10-31 23:59:59+00',
            starts_at = TIMESTAMPTZ '2026-11-02 00:00:00+00',
            ends_at = TIMESTAMPTZ '2026-12-11 23:59:59+00',
            status = 'open',
            updated_at = now()
        WHERE slug = 'cohort-9-blockchain-data'
        """
    )
