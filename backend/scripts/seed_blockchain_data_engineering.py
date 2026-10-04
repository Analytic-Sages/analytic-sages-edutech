#!/usr/bin/env python3
"""Seed / refresh the Blockchain Data Engineering cohort and its full schedule.

Creates the cohort plus the canonical 40-session plan (30 teaching sessions on
Mon/Tue/Wed + 10 Friday office hours) used by the Live Classroom.

Usage (from backend/):
  python scripts/seed_blockchain_data_engineering.py
  python scripts/seed_blockchain_data_engineering.py --reset
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.session import SessionLocal
from app.services.seed_bde_classroom import COHORT_SLUG, seed_bde_classroom


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing sessions for the cohort before reseeding.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        summary = seed_bde_classroom(db, reset=args.reset)
        print(f"Cohort {COHORT_SLUG}: {summary['total']} sessions scheduled")
        print(
            f"  created={summary['created']} updated={summary['updated']} "
            f"deleted={summary['deleted']}"
        )
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
