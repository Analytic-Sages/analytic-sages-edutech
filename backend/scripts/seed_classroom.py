#!/usr/bin/env python3
"""Seed / refresh Cohort 9 + live sessions for Classroom V1.

Usage (from backend/):
  python scripts/seed_classroom.py
  python scripts/seed_classroom.py --email you@example.com
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.classroom import (
    Cohort,
    CohortMember,
    CohortMemberRole,
    CohortStatus,
    LiveSession,
    LiveSessionStatus,
)
from app.models.course import Course
from app.models.user import User

COHORT_SLUG = "cohort-9-blockchain-data"
COURSE_SLUG = "sql-for-blockchain-analytics"

# Cohort 9 marketing dates (UTC midnight on calendar day)
REGISTRATION_DEADLINE = datetime(2026, 9, 30, 23, 59, 59, tzinfo=timezone.utc)
START_DATE = datetime(2026, 10, 1, 0, 0, 0, tzinfo=timezone.utc)
END_DATE = datetime(2026, 11, 30, 23, 59, 59, tzinfo=timezone.utc)
COHORT_PRICE = 35
COHORT_CURRENCY = "USD"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--email",
        default=None,
        help="Optional user email to enroll as cohort student",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        course = db.scalar(select(Course).where(Course.slug == COURSE_SLUG))
        cohort = db.scalar(select(Cohort).where(Cohort.slug == COHORT_SLUG))

        if not cohort:
            cohort = Cohort(
                id=uuid.uuid4(),
                course_id=course.id if course else None,
                name="Cohort 9 - SQL Blockchain Data Analytics",
                slug=COHORT_SLUG,
                description="Onchain Analytics and Research",
                status=CohortStatus.OPEN,
                registration_deadline=REGISTRATION_DEADLINE,
                starts_at=START_DATE,
                ends_at=END_DATE,
                price=COHORT_PRICE,
                currency=COHORT_CURRENCY,
            )
            db.add(cohort)
            db.flush()
            print(f"Created cohort: {cohort.slug}")
        else:
            cohort.name = "Cohort 9 - SQL Blockchain Data Analytics"
            cohort.description = "Onchain Analytics and Research"
            cohort.status = CohortStatus.OPEN
            cohort.registration_deadline = REGISTRATION_DEADLINE
            cohort.starts_at = START_DATE
            cohort.ends_at = END_DATE
            cohort.price = COHORT_PRICE
            cohort.currency = COHORT_CURRENCY
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
                    title="Orientation & SQL Foundations",
                    week_label="Week 1",
                    session_number=1,
                    objectives=[
                        "Meet the cohort",
                        "Set up analytics environment",
                        "Write first on-chain SQL queries",
                    ],
                    resources=[],
                    assignment_summary=None,
                    starts_at=START_DATE.replace(hour=17),
                    ends_at=START_DATE.replace(hour=19),
                    status=LiveSessionStatus.SCHEDULED,
                ),
                LiveSession(
                    id=uuid.uuid4(),
                    cohort_id=cohort.id,
                    title="Onchain Analytics & Research Workflows",
                    week_label="Week 2",
                    session_number=1,
                    objectives=[
                        "Analyze wallet and protocol activity",
                        "Build research-ready dashboards",
                    ],
                    resources=[
                        {
                            "title": "Reading: Onchain research primitives",
                            "url": "https://analyticsages.com",
                            "kind": "reading",
                        }
                    ],
                    assignment_summary=None,
                    starts_at=datetime(2026, 10, 8, 17, 0, tzinfo=timezone.utc),
                    ends_at=datetime(2026, 10, 8, 19, 0, tzinfo=timezone.utc),
                    status=LiveSessionStatus.SCHEDULED,
                ),
            ]
            db.add_all(sessions)
            print(f"Created {len(sessions)} live sessions")
        else:
            print(f"Sessions already exist ({len(existing)})")

        if args.email:
            user = db.scalar(select(User).where(User.email == args.email.lower().strip()))
            if not user:
                print(f"User not found: {args.email}")
            else:
                member = db.scalar(
                    select(CohortMember).where(
                        CohortMember.cohort_id == cohort.id,
                        CohortMember.user_id == user.id,
                    )
                )
                if member:
                    print(f"Already a member: {user.email}")
                else:
                    db.add(
                        CohortMember(
                            id=uuid.uuid4(),
                            cohort_id=cohort.id,
                            user_id=user.id,
                            role=CohortMemberRole.STUDENT,
                        )
                    )
                    print(f"Enrolled {user.email} in {cohort.slug}")

        db.commit()
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
