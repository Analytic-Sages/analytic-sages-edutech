#!/usr/bin/env python3
"""Create the initial admin user.

Usage (from backend/):
  ADMIN_EMAIL=admin@analyticsages.com ADMIN_PASSWORD='secure-password' python scripts/create_admin.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select

from app.core.config import get_settings
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.models.user import User


def main() -> None:
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    full_name = os.environ.get("ADMIN_FULL_NAME", "Platform Admin")

    if not email or not password:
        print("Set ADMIN_EMAIL and ADMIN_PASSWORD environment variables.")
        sys.exit(1)

    if len(password) < 8:
        print("ADMIN_PASSWORD must be at least 8 characters.")
        sys.exit(1)

    settings = get_settings()
    security = SecurityService(settings)
    db = SessionLocal()

    try:
        existing = db.scalar(select(User).where(User.email == email.lower()))
        if existing:
            print(f"Admin user already exists: {email}")
            return

        user = User(
            email=email.lower(),
            password_hash=security.hash_password(password),
            full_name=full_name,
            role=UserRole.ADMIN,
            email_verified=True,
        )
        db.add(user)
        db.commit()
        print(f"Created admin user: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
