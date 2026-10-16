from __future__ import annotations

import re
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.course import Course
from app.models.course_card_placement import CourseCardPlacement
from app.models.user import User

router = APIRouter(tags=["course-card-placements"])
_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,79}$")


class PlacementInput(BaseModel):
    course_id: UUID
    visible: bool = True


class PlacementUpdate(BaseModel):
    placements: list[PlacementInput] = Field(max_length=100)


def _validate_keys(page_key: str, section_key: str) -> None:
    if not _KEY_RE.fullmatch(page_key) or not _KEY_RE.fullmatch(section_key):
        raise HTTPException(status_code=422, detail="Use lowercase letters, numbers, hyphens, and underscores for page and section keys.")


def _row(placement: CourseCardPlacement) -> dict:
    course = placement.course
    return {
        "id": str(placement.id),
        "page_key": placement.page_key,
        "section_key": placement.section_key,
        "course_id": str(course.id),
        "course_slug": course.slug,
        "title": course.title,
        "thumbnail": course.thumbnail,
        "delivery_type": course.delivery_type,
        "published": course.published,
        "sort_order": placement.sort_order,
        "visible": placement.visible,
    }


@router.get("/course-placements/{page_key}/{section_key}")
def public_course_placements(
    page_key: str,
    section_key: str = "main",
    db: Session = Depends(get_db),
) -> list[dict]:
    _validate_keys(page_key, section_key)
    rows = db.scalars(
        select(CourseCardPlacement)
        .join(CourseCardPlacement.course)
        .options(joinedload(CourseCardPlacement.course))
        .where(
            CourseCardPlacement.page_key == page_key,
            CourseCardPlacement.section_key == section_key,
            CourseCardPlacement.visible.is_(True),
            Course.published.is_(True),
        )
        .order_by(CourseCardPlacement.sort_order.asc())
    ).unique().all()
    return [_row(row) for row in rows]


@router.get("/admin/course-placements/options")
def admin_course_placement_options(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    courses = db.scalars(select(Course).order_by(Course.title.asc())).all()
    return [
        {
            "id": str(course.id),
            "slug": course.slug,
            "title": course.title,
            "thumbnail": course.thumbnail,
            "delivery_type": course.delivery_type,
            "published": course.published,
        }
        for course in courses
    ]


@router.get("/admin/course-placements/{page_key}/{section_key}")
def admin_get_course_placements(
    page_key: str,
    section_key: str = "main",
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    _validate_keys(page_key, section_key)
    rows = db.scalars(
        select(CourseCardPlacement)
        .options(joinedload(CourseCardPlacement.course))
        .where(
            CourseCardPlacement.page_key == page_key,
            CourseCardPlacement.section_key == section_key,
        )
        .order_by(CourseCardPlacement.sort_order.asc())
    ).unique().all()
    return [_row(row) for row in rows]


@router.put("/admin/course-placements/{page_key}/{section_key}")
def admin_save_course_placements(
    page_key: str,
    section_key: str,
    payload: PlacementUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    _validate_keys(page_key, section_key)
    ids = [item.course_id for item in payload.placements]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=422, detail="A course can only appear once in a page section.")
    existing_courses = set(db.scalars(select(Course.id).where(Course.id.in_(ids))).all()) if ids else set()
    missing = set(ids) - existing_courses
    if missing:
        raise HTTPException(status_code=422, detail="One or more selected courses no longer exist.")

    # Replace only the selected page/section, leaving every other placement untouched.
    db.query(CourseCardPlacement).filter(
        CourseCardPlacement.page_key == page_key,
        CourseCardPlacement.section_key == section_key,
    ).delete(synchronize_session=False)
    rows = [
        CourseCardPlacement(
            id=uuid4(),
            page_key=page_key,
            section_key=section_key,
            course_id=item.course_id,
            sort_order=index,
            visible=item.visible,
        )
        for index, item in enumerate(payload.placements)
    ]
    db.add_all(rows)
    db.commit()
    saved = db.scalars(
        select(CourseCardPlacement)
        .options(joinedload(CourseCardPlacement.course))
        .where(
            CourseCardPlacement.page_key == page_key,
            CourseCardPlacement.section_key == section_key,
        )
        .order_by(CourseCardPlacement.sort_order.asc())
    ).unique().all()
    return [_row(row) for row in saved]
