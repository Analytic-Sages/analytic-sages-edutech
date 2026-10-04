"""Canonical Blockchain Data Engineering cohort schedule.

The programme runs 10 weeks as 30 teaching sessions (Mon/Tue/Wed) plus a weekly
Friday office hour. This module is the single source of truth the seed script and
the classroom use, mirroring the marketing curriculum in
``frontend/src/lib/blockchain-data-engineering-program.ts`` (5 modules, 30 sessions).

Only the *dates* are computed here; titles, objectives and week projects are data.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.classroom import (
    Cohort,
    CohortStatus,
    LiveSession,
    LiveSessionStatus,
    LiveSessionType,
)
from app.models.course import Course

COHORT_SLUG = "blockchain-data-engineering"
COURSE_SLUG = "blockchain-data-engineering"
COHORT_NAME = "Blockchain Data Engineering"
COHORT_DESCRIPTION = (
    "10-week hands-on programme: build the infrastructure that turns raw blockchain "
    "activity into reliable, usable data systems."
)

# Registration closes 3 Oct 2026; first teaching session is the following Monday.
REGISTRATION_DEADLINE = datetime(2026, 10, 3, 23, 59, 59, tzinfo=timezone.utc)
PROGRAM_START_DATE = date(2026, 10, 5)  # Monday
COHORT_PRICE = 200
COHORT_CURRENCY = "USD"

# West Africa Time has no DST, so the local start time is a stable UTC offset.
WAT = ZoneInfo("Africa/Lagos")
TEACHING_START_HOUR = 18
TEACHING_DURATION_HOURS = 2
OFFICE_HOUR_START_HOUR = 18
OFFICE_HOUR_DURATION_HOURS = 1

TOTAL_WEEKS = 10
TEACHING_WEEKDAYS = (0, 1, 2)  # Monday, Tuesday, Wednesday
OFFICE_HOUR_WEEKDAY = 4  # Friday
SESSIONS_PER_WEEK = 3
TOTAL_TEACHING_SESSIONS = TOTAL_WEEKS * SESSIONS_PER_WEEK  # 30


@dataclass(frozen=True)
class ScheduledSession:
    session_type: LiveSessionType
    session_number: int
    week_number: int
    title: str
    objectives: list[str]
    assignment_summary: str | None
    resources: list[dict] = field(default_factory=list)
    starts_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ends_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def week_label(self) -> str:
        return f"Week {self.week_number}"


OFFICE_HOUR_OBJECTIVES = [
    "Bring questions from the week's build work.",
    "Live debugging, code review and architecture Q&A.",
]
_SESSION_1 = "Programme orientation & systems thinking"
_SESSION_2 = "Python & SQL for data engineers"
_SESSION_3 = "Docker fundamentals for data work"

# Weekly plan mirroring the website curriculum: title, objectives, week project,
# and the three session (title, summary) pairs. Keeps classroom + marketing in sync.
_CURRICULUM: tuple[dict, ...] = (
    {
        "week": 1,
        "objectives": [
            "Understand the Blockchain Data Engineering workflow",
            "Set up a reproducible development environment",
            "Write foundational Python and SQL for pipeline work",
        ],
        "project": None,
        "sessions": [
            (_SESSION_1, "Map the full path from chain data to product and set expectations."),
            (_SESSION_2, "Practical language foundations used throughout the cohort."),
            (_SESSION_3, "Containerise a simple service and understand why reproducibility matters."),
        ],
    },
    {
        "week": 2,
        "objectives": [
            "Connect to blockchain RPC endpoints",
            "Extract transactions, logs and contract events",
            "Persist raw extraction outputs reliably",
        ],
        "project": "Raw extraction service for a chosen contract or token set.",
        "sessions": [
            ("Web3.py & RPC access patterns", "Connect, request and handle blockchain node responses."),
            ("Transactions, receipts and event logs", "Understand the data shapes you will extract and store."),
            ("Building your first extraction job", "Ship a working job that pulls and stores raw onchain data."),
        ],
    },
    {
        "week": 3,
        "objectives": [
            "Design extract, validate and load steps",
            "Run multi-service environments with Docker Compose",
            "Handle failures and retries in batch jobs",
        ],
        "project": None,
        "sessions": [
            ("Pipeline architecture for onchain data", "Break work into dependable stages instead of one-off scripts."),
            ("Docker Compose for data services", "Coordinate application and database containers locally."),
            ("Validation, idempotency and load", "Make ingestion safer to re-run and easier to debug."),
        ],
    },
    {
        "week": 4,
        "objectives": [
            "Apply warehouse concepts to onchain entities",
            "Design schemas for transfers and events",
            "Use indexing to support analytical queries",
        ],
        "project": "Structured warehouse schema for extracted blockchain activity.",
        "sessions": [
            ("Warehouse thinking for blockchain data", "Move from dumping JSON to designing durable tables."),
            ("Schema design for transfers & events", "Normalize addresses, tokens and transfer facts."),
            ("Indexing and query performance basics", "Keep analytical queries usable as volume grows."),
        ],
    },
    {
        "week": 5,
        "objectives": [
            "Structure a dbt project for onchain datasets",
            "Build staging and mart layers",
            "Add tests to transformation models",
        ],
        "project": None,
        "sessions": [
            ("dbt project structure", "Sources, models and the path from raw to marts."),
            ("Staging models for blockchain tables", "Clean and standardize fields before business logic."),
            ("Testing and documenting models", "Make transformations trustworthy and shareable."),
        ],
    },
    {
        "week": 6,
        "objectives": [
            "Normalize addresses and token metadata",
            "Model protocol-relevant entities",
            "Produce datasets ready for analytics and research",
        ],
        "project": "Analytics-ready protocol dataset from your warehouse.",
        "sessions": [
            ("Normalization patterns for onchain data", "Reduce duplication and inconsistency across entities."),
            ("Protocol analytics datasets", "Shape tables that analysts and apps can actually use."),
            ("Review: transformation quality", "Critique models, tests and documentation as a cohort."),
        ],
    },
    {
        "week": 7,
        "objectives": [
            "Express pipelines as orchestrated workflows",
            "Understand Airflow DAGs and dependencies",
            "Handle retries, schedules and observability basics",
        ],
        "project": None,
        "sessions": [
            ("Why orchestration matters", "From manual scripts to dependable scheduled systems."),
            ("Prefect for practical workflows", "Compose flows that match your existing pipeline stages."),
            ("Apache Airflow DAGs", "Model dependencies and schedules with industry-standard tooling."),
        ],
    },
    {
        "week": 8,
        "objectives": [
            "Understand streaming vs batch for blockchain data",
            "Work with Kafka concepts (topics, producers, consumers)",
            "Serve warehouse data through a FastAPI service",
        ],
        "project": "Data API over your analytics-ready tables.",
        "sessions": [
            ("Batch vs streaming for onchain systems", "Choose the right pattern for latency and reliability."),
            ("Apache Kafka fundamentals", "Topics, producers, consumers and where they fit your stack."),
            ("Building blockchain data APIs with FastAPI", "Turn infrastructure into a service applications can call."),
        ],
    },
    {
        "week": 9,
        "objectives": [
            "Package services for cloud deployment",
            "Configure environments and secrets safely",
            "Deploy at least one pipeline or API service",
        ],
        "project": "Deployed service (pipeline worker, API, or both).",
        "sessions": [
            ("Cloud options for data products", "Compare AWS, GCP, Railway and Render for cohort projects."),
            ("Deploying containerised services", "Ship a working service with environment configuration."),
            ("Observability & operational basics", "Logs, health checks and what to watch after deploy."),
        ],
    },
    {
        "week": 10,
        "objectives": [
            "Assemble extraction, warehouse, transform, orchestration and API/deploy",
            "Document architecture decisions",
            "Demo and package work for portfolio use",
        ],
        "project": "End-to-end Blockchain Data Engineering capstone.",
        "sessions": [
            ("Capstone architecture clinic", "Pressure-test designs before the final build push."),
            ("Build & integration lab", "Connect remaining pieces and resolve production issues."),
            ("Demo day & portfolio packaging", "Present what you built and how the system fits together."),
        ],
    },
)


def _local_window(day: date, start_hour: int, duration_hours: int) -> tuple[datetime, datetime]:
    """Return a (start, end) pair in UTC for a local West Africa Time window."""
    start = datetime.combine(day, time(hour=start_hour), tzinfo=WAT)
    end = start + timedelta(hours=duration_hours)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def bde_session_schedule(start: date = PROGRAM_START_DATE) -> list[ScheduledSession]:
    """Build the full 40-row schedule: 30 teaching sessions + 10 Friday office hours.

    ``start`` must be the Monday of week 1 (defaults to 5 Oct 2026).
    """
    if start.weekday() != 0:
        raise ValueError("Programme start date must be a Monday")

    sessions: list[ScheduledSession] = []
    for week_index, week in enumerate(_CURRICULUM):
        week_start = start + timedelta(weeks=week_index)
        week_number = int(week["week"])
        objectives = [str(o) for o in week["objectives"]]
        project = week["project"]

        for day_offset, (title, summary) in zip(TEACHING_WEEKDAYS, week["sessions"], strict=True):
            starts_at, ends_at = _local_window(
                week_start + timedelta(days=day_offset),
                TEACHING_START_HOUR,
                TEACHING_DURATION_HOURS,
            )
            session_number = week_index * SESSIONS_PER_WEEK + day_offset + 1
            sessions.append(
                ScheduledSession(
                    session_type=LiveSessionType.TEACHING,
                    session_number=session_number,
                    week_number=week_number,
                    title=title,
                    objectives=[summary, *objectives],
                    assignment_summary=project,
                    resources=[],
                    starts_at=starts_at,
                    ends_at=ends_at,
                )
            )

        office_start, office_end = _local_window(
            week_start + timedelta(days=OFFICE_HOUR_WEEKDAY),
            OFFICE_HOUR_START_HOUR,
            OFFICE_HOUR_DURATION_HOURS,
        )
        sessions.append(
            ScheduledSession(
                session_type=LiveSessionType.OFFICE_HOUR,
                session_number=week_number,
                week_number=week_number,
                title=f"Office Hour: Open Q&A - Week {week_number}",
                objectives=list(OFFICE_HOUR_OBJECTIVES),
                assignment_summary=None,
                resources=[],
                starts_at=office_start,
                ends_at=office_end,
            )
        )

    return sessions
def _session_key(session_type: LiveSessionType, session_number: int) -> tuple[str, int]:
    return session_type.value, session_number


def seed_bde_classroom(db: Session, *, reset: bool = False) -> dict[str, int]:
    """Create/refresh the BDE cohort and its full schedule. Idempotent.

    Sessions are matched on ``(session_type, session_number)`` so re-running updates
    dates/titles in place, inserts anything missing, and removes the old placeholder
    rows. ``reset=True`` wipes the cohort's sessions first.
    """
    course = db.scalar(select(Course).where(Course.slug == COURSE_SLUG))
    cohort = db.scalar(select(Cohort).where(Cohort.slug == COHORT_SLUG))

    desired = bde_session_schedule()
    starts_at = min(s.starts_at for s in desired)
    ends_at = max(s.ends_at for s in desired)

    if not cohort:
        cohort = Cohort(
            id=uuid.uuid4(),
            course_id=course.id if course else None,
            name=COHORT_NAME,
            slug=COHORT_SLUG,
            description=COHORT_DESCRIPTION,
            status=CohortStatus.OPEN,
            registration_deadline=REGISTRATION_DEADLINE,
            starts_at=starts_at,
            ends_at=ends_at,
            price=COHORT_PRICE,
            currency=COHORT_CURRENCY,
            referral_commission_eligible=True,
        )
        db.add(cohort)
        db.flush()
    else:
        cohort.name = COHORT_NAME
        cohort.description = COHORT_DESCRIPTION
        cohort.status = CohortStatus.OPEN
        cohort.registration_deadline = REGISTRATION_DEADLINE
        cohort.starts_at = starts_at
        cohort.ends_at = ends_at
        cohort.price = COHORT_PRICE
        cohort.currency = COHORT_CURRENCY
        cohort.referral_commission_eligible = True
        if course:
            cohort.course_id = course.id

    existing = list(
        db.scalars(select(LiveSession).where(LiveSession.cohort_id == cohort.id)).all()
    )
    if reset:
        for session in existing:
            db.delete(session)
        db.flush()
        existing = []

    # Collapse any duplicate (type, number) rows left by the old placeholder seed:
    # keep the first, delete the rest.
    by_key: dict[tuple[str, int], LiveSession] = {}
    duplicates: list[LiveSession] = []
    for session in existing:
        key = _session_key(session.session_type, session.session_number)
        if key in by_key:
            duplicates.append(session)
            continue
        by_key[key] = session

    created = 0
    updated = 0

    for item in desired:
        row = by_key.pop(_session_key(item.session_type, item.session_number), None)
        if row is None:
            db.add(
                LiveSession(
                    id=uuid.uuid4(),
                    cohort_id=cohort.id,
                    title=item.title,
                    week_label=item.week_label,
                    session_number=item.session_number,
                    session_type=item.session_type,
                    objectives=item.objectives,
                    resources=item.resources,
                    assignment_summary=item.assignment_summary,
                    starts_at=item.starts_at,
                    ends_at=item.ends_at,
                    status=LiveSessionStatus.SCHEDULED,
                )
            )
            created += 1
            continue

        row.title = item.title
        row.week_label = item.week_label
        row.session_number = item.session_number
        row.session_type = item.session_type
        row.objectives = item.objectives
        row.resources = item.resources
        row.assignment_summary = item.assignment_summary
        row.starts_at = item.starts_at
        row.ends_at = item.ends_at
        updated += 1

    # Anything left in by_key is a stale placeholder no longer in the plan.
    deleted = 0
    for stale in [*by_key.values(), *duplicates]:
        db.delete(stale)
        deleted += 1

    db.commit()
    return {"created": created, "updated": updated, "deleted": deleted, "total": len(desired)}