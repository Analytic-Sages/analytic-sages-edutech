#!/usr/bin/env python3
"""Mark a user email as verified (local / ops helper).

Usage (from backend/):
  python scripts/verify_user.py --email you@example.com
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == args.email.lower().strip()))
        if not user:
            print(f"User not found: {args.email}")
            sys.exit(1)
        user.email_verified = True
        db.commit()
        print(f"Verified: {user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
