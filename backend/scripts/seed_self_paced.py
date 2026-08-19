#!/usr/bin/env python3
"""Seed the first free self-paced course (idempotent).

Usage (from backend/):
  python scripts/seed_self_paced.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.session import SessionLocal
from app.services.seed_self_paced import seed_dune_course


def main() -> None:
    db = SessionLocal()
    try:
        course = seed_dune_course(db)
        db.commit()
        print(f"Seeded self-paced course: {course.slug} ({course.lessons_count} lessons).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
