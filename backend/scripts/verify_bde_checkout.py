#!/usr/bin/env python3
"""Verify BDE cohort + tuition plans are ready for checkout.

Usage (from backend/):
  python scripts/verify_bde_checkout.py

Exit 0 when cohort is open, tuition plans exist, and BILLING_PLANS_ENABLED is true.
"""

from __future__ import annotations

import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.admin import FEATURED_COHORT_SLUG
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.billing import TuitionPlan
from app.models.classroom import Cohort, CohortStatus

EXPECTED_FULL = Decimal("200.00")
EXPECTED_INSTALLMENT_TOTAL = Decimal("220.00")
EXPECTED_INSTALLMENT_EACH = Decimal("110.00")
EXPECTED_PLAN_NAMES = {"Pay in Full", "Pay in 2 Installments"}


def _ok(msg: str) -> None:
    print(f"OK   {msg}")


def _fail(msg: str) -> None:
    print(f"FAIL {msg}")


def main() -> int:
    settings = get_settings()
    failures = 0

    print(f"Cohort slug: {FEATURED_COHORT_SLUG}")
    print(f"BILLING_PLANS_ENABLED: {settings.billing_plans_enabled}")
    print(f"PAYMENT_MODE: {settings.payment_mode}")
    if settings.payment_mode != "live":
        print(
            "NOTE PAYMENT_MODE is not live - checkout uses mock adapters. "
            "Set PAYMENT_MODE=live on Render (with provider secrets) for real charges."
        )
    print()

    if settings.billing_plans_enabled:
        _ok("Billing plans feature flag is enabled")
    else:
        _fail("Set BILLING_PLANS_ENABLED=true on the API service and redeploy")
        failures += 1

    db = SessionLocal()
    try:
        cohort = db.scalar(select(Cohort).where(Cohort.slug == FEATURED_COHORT_SLUG))
        if not cohort:
            _fail(
                f"Cohort {FEATURED_COHORT_SLUG!r} not found — "
                "run python scripts/seed_blockchain_data_engineering.py"
            )
            return 1

        status = cohort.status
        if status in {CohortStatus.OPEN, CohortStatus.ACTIVE}:
            _ok(f"Cohort status is {status.value}")
        else:
            _fail(
                f"Cohort status is {status.value} (need open or active) — "
                "run python scripts/seed_blockchain_data_engineering.py"
            )
            failures += 1

        price = Decimal(str(cohort.price))
        if price == EXPECTED_FULL:
            _ok(f"Cohort price is {price} {cohort.currency}")
        else:
            _fail(f"Cohort price is {price} {cohort.currency} (expected {EXPECTED_FULL})")
            failures += 1

        if cohort.registration_deadline:
            _ok(f"Registration deadline: {cohort.registration_deadline.isoformat()}")
        else:
            _fail("Registration deadline is missing")
            failures += 1

        plans = list(
            db.scalars(
                select(TuitionPlan)
                .options(selectinload(TuitionPlan.schedules))
                .where(TuitionPlan.cohort_id == cohort.id, TuitionPlan.active.is_(True))
            ).all()
        )
        names = {p.name for p in plans}
        if EXPECTED_PLAN_NAMES <= names:
            _ok(f"Active tuition plans: {', '.join(sorted(names))}")
        else:
            missing = EXPECTED_PLAN_NAMES - names
            _fail(
                f"Missing plans {sorted(missing)} — "
                "run python scripts/seed_tuition_plans.py"
            )
            failures += 1

        for plan in plans:
            if plan.name == "Pay in Full":
                amount = Decimal(str(plan.base_amount))
                if amount != EXPECTED_FULL:
                    _fail(f"Pay in Full base_amount={amount} (expected {EXPECTED_FULL})")
                    failures += 1
                elif len(plan.schedules) != 1:
                    _fail(f"Pay in Full should have 1 schedule, has {len(plan.schedules)}")
                    failures += 1
                else:
                    _ok("Pay in Full schedule looks correct")
            elif plan.name == "Pay in 2 Installments":
                amount = Decimal(str(plan.base_amount))
                if amount != EXPECTED_INSTALLMENT_TOTAL:
                    _fail(
                        f"Installments base_amount={amount} "
                        f"(expected {EXPECTED_INSTALLMENT_TOTAL})"
                    )
                    failures += 1
                schedules = sorted(plan.schedules, key=lambda s: s.sequence_number)
                if len(schedules) != 2:
                    _fail(f"Installments should have 2 schedules, has {len(schedules)}")
                    failures += 1
                else:
                    a1 = Decimal(str(schedules[0].amount))
                    a2 = Decimal(str(schedules[1].amount))
                    if a1 == EXPECTED_INSTALLMENT_EACH and a2 == EXPECTED_INSTALLMENT_EACH:
                        _ok("Installment schedule amounts look correct ($110 + $110)")
                    else:
                        _fail(f"Installment amounts are {a1} + {a2}")
                        failures += 1

        print()
        print(f"Cohort id (for /billing/plans): {cohort.id}")
        print(f"Checkout path: /checkout/cohort/{FEATURED_COHORT_SLUG}")
    finally:
        db.close()

    print()
    if failures:
        print(f"Result: {failures} check(s) failed — see docs/bde-checkout-ops.md")
        return 1
    print("Result: ready for BDE checkout with tuition plans")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
