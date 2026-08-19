#!/usr/bin/env python3
"""Seed the first free self-paced course (idempotent).

Usage (from backend/):
  python scripts/seed_self_paced.py
"""

from __future__ import annotations

import os
import sys
import uuid
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.course import Course
from app.models.lms import CourseModule, Lesson

DUNE_SLUG = "dune-analytics-practical-sql-dashboard-techniques"

COURSE = {
    "slug": DUNE_SLUG,
    "title": "Dune Analytics: Practical SQL & Dashboard Techniques",
    "description": (
        "Learn practical techniques for building more powerful blockchain analytics dashboards "
        "with Dune. This free self-paced course covers external API calls, dashboard parameters, "
        "dynamic date filters, custom dashboard images, and handling NULL values in Dune SQL."
    ),
    "long_description": (
        "Learn practical techniques for building more powerful blockchain analytics dashboards "
        "with Dune, from external API calls and dashboard parameters to dynamic date filters "
        "and robust SQL."
    ),
    "thumbnail": "/dune-analytics-practical-sql-dashboard-techniques.png",
    "category": "Blockchain",
    "difficulty": "Beginner to Intermediate",
    "duration": "~70 minutes",
    "estimated_minutes": 70,
    "lessons_count": 6,
    "price": 0,
    "currency": "USD",
    "delivery_type": "self_paced",
    "is_free": True,
    "certificate_enabled": False,
    "published": True,
}

MODULES: list[dict[str, Any]] = [
    {
        "title": "Working With External APIs in Dune",
        "description": "Call external APIs from Dune and use the results in your analytics workflow.",
        "order_index": 1,
        "lessons": [
            {
                "slug": "introduction-to-external-api-calls-in-dune",
                "title": "Introduction to External API Calls in Dune",
                "description": "A short introduction to external API calls in Dune and where they fit in a dashboard workflow.",
                "video_id": "shWx3DDveg0",
                "duration_seconds": 69,
                "order_index": 1,
                "what_you_learn": [
                    "What external API calls are in Dune",
                    "When you might use them in a dashboard workflow",
                ],
                "key_concepts": ["External API calls", "Dune dashboards"],
            },
            {
                "slug": "how-to-use-external-api-calls-in-dune",
                "title": "How to Use External API Calls in Dune",
                "description": "A practical walkthrough of using external API calls in Dune.",
                "video_id": "bhlISIxGpQo",
                "duration_seconds": 1289,
                "order_index": 2,
                "what_you_learn": [
                    "How to make an external API call from Dune",
                    "How those results can feed a query or dashboard",
                ],
                "key_concepts": ["External API calls", "Query results"],
            },
        ],
    },
    {
        "title": "Building Interactive Dune Dashboards",
        "description": "Make dashboards interactive with parameters, images, and dynamic date filters.",
        "order_index": 2,
        "lessons": [
            {
                "slug": "how-to-add-use-dashboard-parameters-in-sql",
                "title": "How to Add & Use Dashboard Parameters in SQL",
                "description": "How dashboard parameters work in Dune and how they can make SQL queries interactive.",
                "video_id": "Ya9ypRLKU5k",
                "duration_seconds": 944,
                "order_index": 1,
                "what_you_learn": [
                    "How dashboard parameters work in Dune",
                    "How parameters can make SQL queries interactive",
                    "How users can control query inputs from a dashboard",
                ],
                "key_concepts": ["Dashboard parameters", "Interactive SQL"],
            },
            {
                "slug": "how-to-add-custom-images-to-dune-analytics-dashboard",
                "title": "How to Add Custom Images to Your Dune Analytics Dashboard",
                "description": "How custom images can support a clearer visual layout on a Dune dashboard.",
                "video_id": "e3SyjYobvlo",
                "duration_seconds": 567,
                "order_index": 2,
                "what_you_learn": [
                    "Where custom images fit on a Dune dashboard",
                    "How images can support a clearer visual layout",
                ],
                "key_concepts": ["Dashboard images", "Visual layout"],
            },
            {
                "slug": "how-to-add-dynamic-date-presets-in-dune-analytics",
                "title": "How to Add Dynamic Date Presets in Dune Analytics",
                "subtitle": "Today / 7D / 30D",
                "description": "How dynamic date presets can keep a Dune dashboard current.",
                "video_id": "wPUXCf-FCAs",
                "duration_seconds": 1250,
                "order_index": 3,
                "what_you_learn": [
                    "How date presets like Today, 7D, and 30D can drive filters",
                    "How dynamic dates keep a dashboard current",
                ],
                "key_concepts": ["Date presets", "Dynamic filters"],
            },
        ],
    },
    {
        "title": "Writing More Robust Dune SQL",
        "description": "Keep Dune SQL reliable when values are missing or undefined.",
        "order_index": 3,
        "lessons": [
            {
                "slug": "how-to-handle-null-values-in-dune-sql",
                "title": "How to Handle NULL Values in Dune SQL",
                "subtitle": "COALESCE, NULLIF & Safe Divide",
                "description": "How NULL handling patterns can keep Dune SQL queries more robust.",
                "video_id": "YtR0k8YY2d4",
                "duration_seconds": None,
                "order_index": 1,
                "what_you_learn": [
                    "How COALESCE, NULLIF, and safe divide patterns help queries stay robust",
                    "Why NULL handling matters in analytics SQL",
                ],
                "key_concepts": ["COALESCE", "NULLIF", "Safe divide", "NULL values"],
            },
        ],
    },
]


def _upsert_lesson(db: Session, course: Course, module: CourseModule, payload: dict[str, Any]) -> None:
    lesson = db.scalar(
        select(Lesson).where(Lesson.course_id == course.id, Lesson.slug == payload["slug"])
    )
    fields = {
        "title": payload["title"],
        "subtitle": payload.get("subtitle"),
        "description": payload["description"],
        "video_provider": "youtube",
        "video_id": payload["video_id"],
        "duration_seconds": payload.get("duration_seconds"),
        "order_index": payload["order_index"],
        "published": True,
        "what_you_learn": payload.get("what_you_learn") or [],
        "key_concepts": payload.get("key_concepts") or [],
        "resources": payload.get("resources") or [],
        "module_id": module.id,
        "course_id": course.id,
    }
    if lesson:
        for key, value in fields.items():
            setattr(lesson, key, value)
        return
    db.add(Lesson(id=uuid.uuid4(), slug=payload["slug"], **fields))


def seed_dune_course(db: Session) -> Course:
    course = db.scalar(select(Course).where(Course.slug == DUNE_SLUG))
    if course:
        for key, value in COURSE.items():
            setattr(course, key, value)
    else:
        course = Course(id=uuid.uuid4(), **COURSE)
        db.add(course)
        db.flush()

    existing_modules = {module.order_index: module for module in course.modules}
    for module_payload in MODULES:
        module = existing_modules.get(module_payload["order_index"])
        if module:
            module.title = module_payload["title"]
            module.description = module_payload["description"]
        else:
            module = CourseModule(
                id=uuid.uuid4(),
                course_id=course.id,
                title=module_payload["title"],
                description=module_payload["description"],
                order_index=module_payload["order_index"],
            )
            db.add(module)
            db.flush()
        for lesson_payload in module_payload["lessons"]:
            _upsert_lesson(db, course, module, lesson_payload)

    db.flush()
    return course


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
