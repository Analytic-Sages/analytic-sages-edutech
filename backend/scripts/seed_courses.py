#!/usr/bin/env python3
"""Seed published courses for checkout (from frontend mock catalog).

Usage (from backend/):
  python scripts/seed_courses.py
"""

import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.course import Course

# Live enrollable: SQL ($35) and Python ($150). Others: price 0 = launching soon.
COURSES = [
    {
        "slug": "applied-ai-for-blockchain",
        "title": "Applied AI for Blockchain",
        "description": "Apply machine learning and AI techniques to on-chain data, smart contracts, and DeFi protocol analysis.",
        "thumbnail": "/applied-ai-for-blockchain.png",
        "category": "AI",
        "difficulty": "Intermediate",
        "duration": "10 weeks",
        "lessons_count": 40,
        "price": 0,
        "currency": "USD",
    },
    {
        "slug": "sql-for-blockchain-analytics",
        "title": "Beginner Blockchain Analytics (SQL)",
        "description": "Master Dune, Flipside, and advanced SQL to query blockchain data like professional analysts.",
        "thumbnail": "/sql-for-blockchain-analytics.png",
        "category": "Blockchain",
        "difficulty": "Beginner",
        "duration": "4 weeks",
        "lessons_count": 18,
        "price": 35,
        "currency": "USD",
    },
    {
        "slug": "tableau-for-web3-business-intelligence",
        "title": "Tableau for Web3 Business Intelligence",
        "description": "Turn on-chain data into clear dashboards and business insights with Tableau, built for Web3 teams and analysts.",
        "thumbnail": "/1.png",
        "category": "Blockchain",
        "difficulty": "Beginner",
        "duration": "2 months",
        "lessons_count": 20,
        "price": 0,
        "currency": "USD",
    },
    {
        "slug": "python-for-blockchain-analytics",
        "title": "Python for Blockchain Data Analytics",
        "description": "Build blockchain data pipelines, automate workflows, and analyze onchain activity with Python.",
        "thumbnail": "/python-for-blockchain-analytics.png",
        "category": "Blockchain",
        "difficulty": "Beginner",
        "duration": "2 months",
        "lessons_count": 20,
        "price": 150,
        "currency": "USD",
    },
    {
        "slug": "blockchain-data-engineering",
        "title": "Blockchain Data Engineering",
        "description": "Learn how modern blockchain datasets are collected, transformed, and served at scale.",
        "thumbnail": "/blockchain-data-engineering.png",
        "category": "Data Engineering",
        "difficulty": "Intermediate",
        "duration": "12 weeks",
        "lessons_count": 44,
        "price": 0,
        "currency": "USD",
    },
    {
        "slug": "quantitative-trading-with-python",
        "title": "Quantitative Trading with Python",
        "description": "Build, backtest, and evaluate crypto trading strategies using Python and quantitative methods.",
        "thumbnail": "/quantitative-trading-with-python.png",
        "category": "Quantitative Finance",
        "difficulty": "Advanced",
        "duration": "10 weeks",
        "lessons_count": 38,
        "price": 0,
        "currency": "USD",
    },
]

LIVE_SLUGS = {
    "sql-for-blockchain-analytics",
    "python-for-blockchain-analytics",
}


def main() -> None:
    db = SessionLocal()
    created = 0
    try:
        for item in COURSES:
            existing = db.scalar(select(Course).where(Course.slug == item["slug"]))
            if existing:
                existing.price = item["price"]
                existing.currency = item["currency"]
                existing.published = True
                existing.title = item["title"]
                existing.description = item["description"]
                existing.thumbnail = item["thumbnail"]
                existing.category = item["category"]
                existing.difficulty = item["difficulty"]
                existing.duration = item["duration"]
                existing.lessons_count = item["lessons_count"]
                continue

            db.add(
                Course(
                    id=uuid.uuid4(),
                    published=True,
                    **item,
                )
            )
            created += 1
        from app.services.seed_self_paced import seed_dune_course

        seed_dune_course(db)
        db.commit()
        print(f"Seeded courses. Newly created: {created}. Total catalog: {len(COURSES)}.")
        print(f"Live for checkout: {', '.join(sorted(LIVE_SLUGS))}.")
        print("Seeded free self-paced course: dune-analytics-practical-sql-dashboard-techniques.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
