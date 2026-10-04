"""Idempotent seed for the featured free self-paced Dune course."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.course import Course
from app.models.lms import CourseModule, Lesson
from app.models.quiz import Quiz, QuizOption, QuizQuestion

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


def unpublish_pytest_courses(db: Session) -> None:
    leftovers = db.scalars(
        select(Course).where(Course.published.is_(True), Course.slug.like("test-%"))
    ).all()
    for course in leftovers:
        course.published = False


QUIZZES: dict[int, dict[str, Any]] = {
    1: {
        "title": "Module 1 Quiz: External API Calls in Dune",
        "pass_score": 67,
        "questions": [
            {
                "prompt": "What does an external API call let a Dune query do?",
                "options": [
                    ("Pull off-chain data (e.g. prices, metadata) into the query", True),
                    ("Mint new tokens on-chain", False),
                    ("Change past block rewards", False),
                ],
                "explanation": (
                    "External API calls bring data from services outside the blockchain "
                    "into Dune SQL."
                ),
            },
            {
                "prompt": "Why keep the number of external calls in a Dune query low?",
                "options": [
                    ("Because each call adds latency and counts against query limits", True),
                    ("Because Dune only allows network requests at midnight", False),
                    ("Because calls delete your saved dashboards", False),
                ],
                "explanation": "External calls are slower and rate-limited, so batch or cache them.",
            },
        ],
    },
    2: {
        "title": "Module 2 Quiz: Interactive Dune Dashboards",
        "pass_score": 67,
        "questions": [
            {
                "prompt": "What do dashboard parameters let you do in Dune SQL?",
                "options": [
                    ("Let viewers change a value without editing the query", True),
                    ("Permanently modify the underlying blockchain data", False),
                    ("Disable the query cache", False),
                ],
                "explanation": "Parameters expose inputs so viewers can filter charts themselves.",
            },
            {
                "prompt": "Which is the best way to keep a dashboard's dates current?",
                "options": [
                    ("Use dynamic date presets / relative ranges", True),
                    ("Hard-code fixed dates for every chart", False),
                    ("Recreate the dashboard each week by hand", False),
                ],
                "explanation": "Dynamic date presets keep charts fresh without manual edits.",
            },
        ],
    },
    3: {
        "title": "Module 3 Quiz: Writing More Robust Dune SQL",
        "pass_score": 67,
        "questions": [
            {
                "prompt": "Which pattern safely handles NULL values in Dune SQL?",
                "options": [
                    ("COALESCE(value, fallback)", True),
                    ("CONVERT(value, NULL)", False),
                    ("DELETE FROM value WHERE NULL", False),
                ],
                "explanation": "COALESCE replaces NULLs with a fallback value.",
            },
            {
                "prompt": "Why should you guard against dividing by zero in SQL?",
                "options": [
                    ("Division by zero errors out or returns invalid results", True),
                    ("SQL silently returns 1 for any division by zero", False),
                    ("Zero denominators make queries run forever", False),
                ],
                "explanation": "Use NULLIF on the denominator, then COALESCE the result.",
            },
        ],
    },
}


def seed_dune_course(db: Session) -> Course:
    unpublish_pytest_courses(db)
    course = db.scalar(
        select(Course)
        .options(selectinload(Course.modules).selectinload(CourseModule.lessons))
        .where(Course.slug == DUNE_SLUG)
    )
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

    seed_dune_quizzes(db, course)
    db.flush()
    return course


def seed_dune_quizzes(db: Session, course: Course) -> None:
    """Idempotently attach one module quiz to each Dune module."""
    modules = {
        module.order_index: module
        for module in db.scalars(
            select(CourseModule).where(CourseModule.course_id == course.id)
        ).all()
    }
    for order_index, payload in QUIZZES.items():
        module = modules.get(order_index)
        if not module:
            continue
        quiz = db.scalar(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.course_id == course.id, Quiz.module_id == module.id)
        )
        if quiz:
            quiz.title = payload["title"]
            quiz.pass_score = payload["pass_score"]
            quiz.published = True
        else:
            quiz = Quiz(
                id=uuid.uuid4(),
                course_id=course.id,
                module_id=module.id,
                title=payload["title"],
                description="",
                pass_score=payload["pass_score"],
                published=True,
                order_index=order_index,
            )
            db.add(quiz)
            db.flush()

        for question in list(quiz.questions):
            db.delete(question)
        db.flush()

        for question_index, question_payload in enumerate(payload["questions"], start=1):
            question = QuizQuestion(
                id=uuid.uuid4(),
                quiz_id=quiz.id,
                prompt=question_payload["prompt"],
                explanation=question_payload.get("explanation"),
                order_index=question_index,
            )
            db.add(question)
            db.flush()
            for option_index, (label, is_correct) in enumerate(
                question_payload["options"], start=1
            ):
                db.add(
                    QuizOption(
                        id=uuid.uuid4(),
                        question_id=question.id,
                        label=label,
                        is_correct=is_correct,
                        order_index=option_index,
                    )
                )
    db.flush()
