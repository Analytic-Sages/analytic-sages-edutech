from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.course_card_placement import CourseCardPlacement
from app.models.user import User
from app.schemas.course_card_placements import (
    CourseCardPlacementReplace,
    CourseCardPlacementRow,
)

router = APIRouter(tags=["course-card-placements"])


@router.get("/course-card-placements", response_model=list[CourseCardPlacementRow])
def list_public_placements(
    page_key: str,
    section_key: str,
    db: Session = Depends(get_db),
):
    """Public, read-only placement config used by marketing page card sections."""
    return db.scalars(
        select(CourseCardPlacement)
        .where(
            CourseCardPlacement.page_key == page_key,
            CourseCardPlacement.section_key == section_key,
            CourseCardPlacement.visible.is_(True),
        )
        .order_by(CourseCardPlacement.position, CourseCardPlacement.created_at)
    ).all()


@router.get("/admin/course-card-placements", response_model=list[CourseCardPlacementRow])
def list_admin_placements(
    page_key: str | None = None,
    section_key: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = select(CourseCardPlacement)
    if page_key:
        query = query.where(CourseCardPlacement.page_key == page_key)
    if section_key:
        query = query.where(CourseCardPlacement.section_key == section_key)
    return db.scalars(
        query.order_by(
            CourseCardPlacement.page_key,
            CourseCardPlacement.section_key,
            CourseCardPlacement.position,
        )
    ).all()


@router.put("/admin/course-card-placements", response_model=list[CourseCardPlacementRow])
def replace_placements(
    payload: CourseCardPlacementReplace,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    keys = [item.card_key for item in payload.placements]
    if len(keys) != len(set(keys)):
        raise HTTPException(status_code=422, detail="A card can only appear once in a page section.")
    existing = db.scalars(
        select(CourseCardPlacement).where(
            CourseCardPlacement.page_key == payload.page_key,
            CourseCardPlacement.section_key == payload.section_key,
        )
    ).all()
    for row in existing:
        db.delete(row)
    db.flush()
    rows = [
        CourseCardPlacement(
            page_key=payload.page_key,
            section_key=payload.section_key,
            card_key=item.card_key,
            position=index,
            visible=item.visible,
        )
        for index, item in enumerate(payload.placements)
    ]
    db.add_all(rows)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows
