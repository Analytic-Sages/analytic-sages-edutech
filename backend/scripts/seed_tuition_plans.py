#!/usr/bin/env python3
"""Seed tuition plans for the featured cohort (Pay in Full + 2 installments).

Usage (from backend/):
  python scripts/seed_tuition_plans.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.billing import DueRule, TuitionPlanType
from app.core.admin import FEATURED_COHORT_SLUG
from app.db.session import SessionLocal
from app.models.billing import TuitionPlan
from app.models.classroom import Cohort
from app.schemas.billing import TuitionPlanCreate, TuitionPlanScheduleCreate
from app.services.tuition_plans import TuitionPlanService

# BDE tuition (seeded, not hardcoded in checkout logic).
PAY_IN_FULL = Decimal("200.00")
INSTALLMENT_TOTAL = Decimal("220.00")
INSTALLMENT_EACH = Decimal("110.00")


def main() -> None:
    db = SessionLocal()
    try:
        cohort = db.scalar(select(Cohort).where(Cohort.slug == FEATURED_COHORT_SLUG))
        if not cohort:
            print(f"Cohort {FEATURED_COHORT_SLUG} not found. Run seed_blockchain_data_engineering.py first.")
            return

        second_due = None
        if cohort.starts_at:
            # Default: second installment due at week 3 of the cohort.
            second_due = cohort.starts_at + timedelta(weeks=2)
        else:
            second_due = datetime.now(timezone.utc) + timedelta(days=21)

        existing = list(
            db.scalars(
                select(TuitionPlan)
                .options(selectinload(TuitionPlan.schedules))
                .where(TuitionPlan.cohort_id == cohort.id)
            ).all()
        )
        by_name = {p.name: p for p in existing}
        service = TuitionPlanService(db)

        if "Pay in Full" not in by_name:
            service.create_plan(
                TuitionPlanCreate(
                    cohort_id=cohort.id,
                    course_id=cohort.course_id,
                    name="Pay in Full",
                    description="Pay the full tuition once and unlock your seat immediately.",
                    plan_type=TuitionPlanType.ONE_TIME,
                    base_currency="USD",
                    base_amount=PAY_IN_FULL,
                    sort_order=0,
                    schedules=[
                        TuitionPlanScheduleCreate(
                            sequence_number=1,
                            label="Full tuition",
                            amount=PAY_IN_FULL,
                            due_rule=DueRule.IMMEDIATE,
                        )
                    ],
                )
            )
            print("Created plan: Pay in Full")
        else:
            print("Plan exists: Pay in Full")

        if "Pay in 2 Installments" not in by_name:
            service.create_plan(
                TuitionPlanCreate(
                    cohort_id=cohort.id,
                    course_id=cohort.course_id,
                    name="Pay in 2 Installments",
                    description=(
                        "Pay $110 now to unlock your seat, then $110 later "
                        f"(total ${INSTALLMENT_TOTAL})."
                    ),
                    plan_type=TuitionPlanType.INSTALLMENT,
                    base_currency="USD",
                    base_amount=INSTALLMENT_TOTAL,
                    sort_order=1,
                    schedules=[
                        TuitionPlanScheduleCreate(
                            sequence_number=1,
                            label="Installment 1",
                            amount=INSTALLMENT_EACH,
                            due_rule=DueRule.IMMEDIATE,
                        ),
                        TuitionPlanScheduleCreate(
                            sequence_number=2,
                            label="Installment 2",
                            amount=INSTALLMENT_EACH,
                            due_rule=DueRule.SPECIFIC_DATE,
                            due_date=second_due,
                        ),
                    ],
                )
            )
            print("Created plan: Pay in 2 Installments")
        else:
            plan = by_name["Pay in 2 Installments"]
            second = next((s for s in plan.schedules if s.sequence_number == 2), None)
            if second and second_due and second.due_date != second_due:
                second.due_date = second_due
                db.commit()
                print(f"Updated installment 2 due date -> {second_due.isoformat()}")
            else:
                print("Plan exists: Pay in 2 Installments")

        print("Done. Enable with BILLING_PLANS_ENABLED=true and PAYMENT_MODE=live for production.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
