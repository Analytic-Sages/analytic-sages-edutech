"""Schedule the six-week SQL & Excel Cohort 1 timetable.

Revision ID: 045_sql_excel_cohort_sessions
Revises: 044_sql_excel_cohort_launch
Create Date: 2026-10-15
"""

from typing import Sequence, Union

from alembic import op

revision: str = "045_sql_excel_cohort_sessions"
down_revision: Union[str, Sequence[str], None] = "044_sql_excel_cohort_launch"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove only stale, unreferenced seed sessions before the cohort launch.
    # Keep any session linked to attendance, assignments, or recordings.
    op.execute(
        """
        DELETE FROM live_sessions AS s
        USING cohorts AS c
        WHERE s.cohort_id = c.id
          AND c.slug = 'cohort-9-blockchain-data'
          AND s.starts_at < TIMESTAMPTZ '2026-11-02 00:00:00+00'
          AND NOT EXISTS (SELECT 1 FROM attendance a WHERE a.session_id = s.id)
          AND NOT EXISTS (SELECT 1 FROM assignments a WHERE a.session_id = s.id)
          AND NOT EXISTS (SELECT 1 FROM session_recordings r WHERE r.session_id = s.id)
        """
    )

    # If a pre-existing session has learner records, preserve the records while
    # moving the old session out of the active timetable so the new schedule can
    # use the intended session numbers.
    op.execute(
        """
        UPDATE live_sessions AS s
        SET
            title = 'Archived legacy session — ' || s.title,
            week_label = 'Legacy',
            session_number = 1000 + s.session_number,
            status = 'cancelled',
            updated_at = now()
        FROM cohorts AS c
        WHERE s.cohort_id = c.id
          AND c.slug = 'cohort-9-blockchain-data'
          AND s.starts_at < TIMESTAMPTZ '2026-11-02 00:00:00+00'
        """
    )

    op.execute(
        """
        WITH schedule(
            title, week_label, session_number, session_type, objectives,
            assignment_summary, starts_at, ends_at
        ) AS (
            VALUES
            (
                'Orientation, Workspace Setup & Blockchain Research Workflow',
                'Week 1', 1, 'teaching',
                '["Set up the analytics workspace","Understand the course workflow and project expectations","Connect blockchain data questions to research outputs"]'::jsonb,
                'Set up your workspace and write down three research questions to investigate during the cohort.',
                TIMESTAMPTZ '2026-11-02 17:00:00+00', TIMESTAMPTZ '2026-11-02 19:00:00+00'
            ),
            (
                'SQL Foundations: SELECT, WHERE, ORDER BY & LIMIT',
                'Week 1', 2, 'teaching',
                '["Read blockchain datasets with SELECT","Filter and sort records","Build a first reproducible query"]'::jsonb,
                'Submit a short SQL notebook with five useful queries and a sentence explaining each result.',
                TIMESTAMPTZ '2026-11-04 17:00:00+00', TIMESTAMPTZ '2026-11-04 19:00:00+00'
            ),
            (
                'Aggregations, GROUP BY, HAVING & Onchain Metrics',
                'Week 2', 3, 'teaching',
                '["Aggregate transaction and protocol activity","Calculate counts, volumes and averages","Define and validate core metrics"]'::jsonb,
                'Create a metric table for a protocol or ecosystem and document each metric definition.',
                TIMESTAMPTZ '2026-11-09 17:00:00+00', TIMESTAMPTZ '2026-11-09 19:00:00+00'
            ),
            (
                'Joins, CTEs & Multi-Table Blockchain Analysis',
                'Week 2', 4, 'teaching',
                '["Join related blockchain tables","Structure complex queries with CTEs","Check joins for duplicated or missing records"]'::jsonb,
                'Build a multi-table query and include a basic validation check for row counts.',
                TIMESTAMPTZ '2026-11-11 17:00:00+00', TIMESTAMPTZ '2026-11-11 19:00:00+00'
            ),
            (
                'Window Functions, Time Series & Cohort Metrics',
                'Week 3', 5, 'teaching',
                '["Use ranking and window functions","Compare activity across time periods","Build retention or cohort-style metrics"]'::jsonb,
                'Produce a time-series analysis with a clear interpretation of the main trend.',
                TIMESTAMPTZ '2026-11-16 17:00:00+00', TIMESTAMPTZ '2026-11-16 19:00:00+00'
            ),
            (
                'Excel for Analysts: Cleaning, Formulas, Tables & Lookups',
                'Week 3', 6, 'teaching',
                '["Clean inconsistent datasets","Use formulas and lookup functions","Create an auditable analysis workbook"]'::jsonb,
                'Submit a cleaned Excel workbook with formulas and a brief data-quality checklist.',
                TIMESTAMPTZ '2026-11-18 17:00:00+00', TIMESTAMPTZ '2026-11-18 19:00:00+00'
            ),
            (
                'PivotTables, Charts & Analytical Dashboards in Excel',
                'Week 4', 7, 'teaching',
                '["Summarize data with PivotTables","Choose charts that answer specific questions","Design a readable analytical dashboard"]'::jsonb,
                'Build a one-page Excel dashboard with at least three useful metrics and a short insight summary.',
                TIMESTAMPTZ '2026-11-23 17:00:00+00', TIMESTAMPTZ '2026-11-23 19:00:00+00'
            ),
            (
                'Market Data APIs: CoinGecko & Excel Integration',
                'Week 4', 8, 'teaching',
                '["Retrieve market data from an API","Combine price and onchain datasets","Document refresh and data limitations"]'::jsonb,
                'Integrate market data with an analytical dataset and explain how the workbook can be refreshed.',
                TIMESTAMPTZ '2026-11-25 17:00:00+00', TIMESTAMPTZ '2026-11-25 19:00:00+00'
            ),
            (
                'DeFi Protocol Analytics: TVL, Deposits, Withdrawals & Netflows',
                'Week 5', 9, 'teaching',
                '["Analyze protocol activity and TVL","Calculate deposits, withdrawals and netflows","Validate findings against source dashboards"]'::jsonb,
                'Create a concise DeFi protocol analysis using SQL and Excel, including source links and caveats.',
                TIMESTAMPTZ '2026-11-30 17:00:00+00', TIMESTAMPTZ '2026-11-30 19:00:00+00'
            ),
            (
                'RWA, Tokenized Assets & Perpetual Futures Research',
                'Week 5', 10, 'teaching',
                '["Identify useful metrics for tokenized assets","Analyze perpetual futures market structure","Compare metrics across platforms responsibly"]'::jsonb,
                'Write a one-page research brief comparing a selected tokenized asset or derivatives market.',
                TIMESTAMPTZ '2026-12-02 17:00:00+00', TIMESTAMPTZ '2026-12-02 19:00:00+00'
            ),
            (
                'AI-Assisted Analysis: Query Drafting, Validation & Research',
                'Week 6', 11, 'teaching',
                '["Use AI to draft and debug SQL and Excel formulas","Verify generated work against source data","Document assumptions and limitations"]'::jsonb,
                'Submit one AI-assisted analysis with the prompt, validation steps, and corrections documented.',
                TIMESTAMPTZ '2026-12-07 17:00:00+00', TIMESTAMPTZ '2026-12-07 19:00:00+00'
            ),
            (
                'Capstone Workshop: SQL, Excel, Dashboard & Research Brief',
                'Week 6', 12, 'teaching',
                '["Integrate SQL and Excel outputs","Present a dashboard and evidence-backed insight","Prepare the final portfolio deliverables"]'::jsonb,
                'Finalize your capstone package: SQL queries, Excel workbook, dashboard, research report, and presentation.',
                TIMESTAMPTZ '2026-12-09 17:00:00+00', TIMESTAMPTZ '2026-12-09 19:00:00+00'
            ),
            (
                'Week 1 Office Hours & Setup Support',
                'Week 1', 1, 'office_hour',
                '["Resolve setup and access issues","Review first SQL queries","Answer questions about the project workflow"]'::jsonb,
                NULL,
                TIMESTAMPTZ '2026-11-06 17:00:00+00', TIMESTAMPTZ '2026-11-06 18:00:00+00'
            ),
            (
                'Week 2 Office Hours: SQL Queries & Metrics',
                'Week 2', 2, 'office_hour',
                '["Debug joins and aggregations","Review metric definitions","Discuss query validation"]'::jsonb,
                NULL,
                TIMESTAMPTZ '2026-11-13 17:00:00+00', TIMESTAMPTZ '2026-11-13 18:00:00+00'
            ),
            (
                'Week 3 Office Hours: Excel & Data Quality',
                'Week 3', 3, 'office_hour',
                '["Troubleshoot formulas and lookups","Review data cleaning","Get feedback on time-series analysis"]'::jsonb,
                NULL,
                TIMESTAMPTZ '2026-11-20 17:00:00+00', TIMESTAMPTZ '2026-11-20 18:00:00+00'
            ),
            (
                'Week 4 Office Hours: APIs & Dashboards',
                'Week 4', 4, 'office_hour',
                '["Troubleshoot API integration","Review PivotTables and charts","Improve dashboard clarity"]'::jsonb,
                NULL,
                TIMESTAMPTZ '2026-11-27 17:00:00+00', TIMESTAMPTZ '2026-11-27 18:00:00+00'
            ),
            (
                'Week 5 Office Hours: DeFi, RWA & Derivatives Research',
                'Week 5', 5, 'office_hour',
                '["Review research metrics","Check source quality and assumptions","Get feedback on the research brief"]'::jsonb,
                NULL,
                TIMESTAMPTZ '2026-12-04 17:00:00+00', TIMESTAMPTZ '2026-12-04 18:00:00+00'
            ),
            (
                'Week 6 Office Hours: Capstone Review & Final Questions',
                'Week 6', 6, 'office_hour',
                '["Review capstone progress","Resolve final SQL and Excel issues","Prepare final presentation and submission"]'::jsonb,
                NULL,
                TIMESTAMPTZ '2026-12-11 17:00:00+00', TIMESTAMPTZ '2026-12-11 18:00:00+00'
            )
        )
        INSERT INTO live_sessions (
            id, cohort_id, title, week_label, session_number, session_type,
            objectives, resources, assignment_summary, description, timezone,
            starts_at, ends_at, status
        )
        SELECT
            gen_random_uuid(),
            c.id,
            schedule.title,
            schedule.week_label,
            schedule.session_number,
            schedule.session_type::live_session_type,
            schedule.objectives,
            '[]'::jsonb,
            schedule.assignment_summary,
            'SQL & Excel Cohort 1 scheduled session',
            'Africa/Lagos',
            schedule.starts_at,
            schedule.ends_at,
            'scheduled'::live_session_status
        FROM cohorts AS c
        CROSS JOIN schedule
        WHERE c.slug = 'cohort-9-blockchain-data'
          AND NOT EXISTS (
              SELECT 1
              FROM live_sessions AS existing
              WHERE existing.cohort_id = c.id
                AND existing.session_type = schedule.session_type::live_session_type
                AND existing.session_number = schedule.session_number
          )
        """
    )


def downgrade() -> None:
    # Remove only the sessions created by this migration.
    op.execute(
        """
        DELETE FROM live_sessions AS s
        USING cohorts AS c
        WHERE s.cohort_id = c.id
          AND c.slug = 'cohort-9-blockchain-data'
          AND s.description = 'SQL & Excel Cohort 1 scheduled session'
        """
    )
