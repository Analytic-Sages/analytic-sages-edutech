#!/usr/bin/env python3
"""Seed / refresh Blockchain Data Engineering instructor-led cohort.

Usage (from backend/):
  python scripts/seed_blockchain_data_engineering.py
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.classroom import Cohort, CohortStatus, LiveSession, LiveSessionStatus
from app.models.course import Course

COHORT_SLUG = "blockchain-data-engineering"
COURSE_SLUG = "blockchain-data-engineering"
COHORT_NAME = "Blockchain Data Engineering"
COHORT_DESCRIPTION = (
    "10-week hands-on programme: build the infrastructure that turns raw blockchain "
    "activity into reliable, usable data systems."
)

# Registration open from 4 Sep 2026. Deadline 3 Oct 2026 (after open date).
# Programme runs 10 weeks from the first live week after registration closes.
REGISTRATION_DEADLINE = datetime(2026, 10, 3, 23, 59, 59, tzinfo=timezone.utc)
START_DATE = datetime(2026, 10, 6, 0, 0, 0, tzinfo=timezone.utc)
END_DATE = datetime(2026, 12, 14, 23, 59, 59, tzinfo=timezone.utc)
COHORT_PRICE = 200
COHORT_CURRENCY = "USD"


def main() -> None:
    db = SessionLocal()
    try:
        course = db.scalar(select(Course).where(Course.slug == COURSE_SLUG))
        cohort = db.scalar(select(Cohort).where(Cohort.slug == COHORT_SLUG))

        if not cohort:
            cohort = Cohort(
                id=uuid.uuid4(),
                course_id=course.id if course else None,
                name=COHORT_NAME,
                slug=COHORT_SLUG,
                description=COHORT_DESCRIPTION,
                status=CohortStatus.OPEN,
                registration_deadline=REGISTRATION_DEADLINE,
                starts_at=START_DATE,
                ends_at=END_DATE,
                price=COHORT_PRICE,
                currency=COHORT_CURRENCY,
                referral_commission_eligible=True,
            )
            db.add(cohort)
            db.flush()
            print(f"Created cohort: {cohort.slug}")
        else:
            cohort.name = COHORT_NAME
            cohort.description = COHORT_DESCRIPTION
            cohort.status = CohortStatus.OPEN
            cohort.registration_deadline = REGISTRATION_DEADLINE
            cohort.starts_at = START_DATE
            cohort.ends_at = END_DATE
            cohort.price = COHORT_PRICE
            cohort.currency = COHORT_CURRENCY
            cohort.referral_commission_eligible = True
            if course:
                cohort.course_id = course.id
            print(f"Updated cohort: {cohort.slug}")

        existing = list(
            db.scalars(select(LiveSession).where(LiveSession.cohort_id == cohort.id)).all()
        )
        if not existing:
            sessions = [
                LiveSession(
                    id=uuid.uuid4(),
                    cohort_id=cohort.id,
                    title="Orientation & Reproducible Environments",
                    week_label="Week 1",
                    session_number=1,
                    objectives=[
                        "Programme overview and engineering workflow",
                        "Local tooling and Docker fundamentals",
                        "First containerized service",
                    ],
                    resources=[],
                    assignment_summary="Set up Docker and run a baseline containerized environment.",
                    starts_at=START_DATE.replace(hour=17),
                    ends_at=START_DATE.replace(hour=19),
                    status=LiveSessionStatus.SCHEDULED,
                ),
                LiveSession(
                    id=uuid.uuid4(),
                    cohort_id=cohort.id,
                    title="Containerized Ingestion Pipelines",
                    week_label="Week 2",
                    session_number=1,
                    objectives=[
                        "Structure a data ingestion service",
                        "Compose multi-service environments",
                        "Connect application containers to PostgreSQL",
                    ],
                    resources=[],
                    assignment_summary="Ship a reproducible ingestion pipeline with Docker Compose.",
                    starts_at=datetime(2026, 10, 27, 17, 0, tzinfo=timezone.utc),
                    ends_at=datetime(2026, 10, 27, 19, 0, tzinfo=timezone.utc),
                    status=LiveSessionStatus.SCHEDULED,
                ),
            ]
            db.add_all(sessions)
            print(f"Created {len(sessions)} live sessions")
        else:
            print(f"Sessions already exist ({len(existing)})")

        db.commit()
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
