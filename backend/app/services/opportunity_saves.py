from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.opportunity import (
    CareerPath,
    Opportunity,
    OpportunityCareerPath,
    OpportunitySave,
    OpportunitySaveState,
    OpportunitySkill,
    OpportunityStatus,
    UserCareerInterest,
)
from app.models.user import User
from app.schemas.opportunities import (
    CareerPathPublic,
    OpportunityCardPublic,
    OpportunitySaveList,
    OpportunitySavePublic,
    UserCareerInterestsPublic,
)
from app.services.opportunities import OpportunityService


class OpportunityEngagementService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.opportunities = OpportunityService(db)

    def _utcnow(self) -> datetime:
        return datetime.now(UTC)

    def save_map(self, user: User, opportunity_ids: list[UUID]) -> dict[UUID, OpportunitySave]:
        if not opportunity_ids:
            return {}
        rows = self.db.scalars(
            select(OpportunitySave).where(
                OpportunitySave.user_id == user.id,
                OpportunitySave.opportunity_id.in_(opportunity_ids),
            )
        ).all()
        return {row.opportunity_id: row for row in rows}

    def interest_path_ids(self, user: User) -> list[UUID]:
        return list(
            self.db.scalars(
                select(UserCareerInterest.career_path_id).where(UserCareerInterest.user_id == user.id)
            ).all()
        )

    def get_interests(self, user: User) -> UserCareerInterestsPublic:
        rows = self.db.scalars(
            select(UserCareerInterest)
            .options(selectinload(UserCareerInterest.career_path))
            .where(UserCareerInterest.user_id == user.id)
        ).all()
        return UserCareerInterestsPublic(
            career_paths=[
                CareerPathPublic(
                    id=row.career_path.id,
                    name=row.career_path.name,
                    slug=row.career_path.slug,
                    description=row.career_path.description,
                )
                for row in rows
                if row.career_path
            ]
        )

    def set_interests(self, user: User, career_path_ids: list[UUID]) -> UserCareerInterestsPublic:
        unique_ids = list(dict.fromkeys(career_path_ids))
        if unique_ids:
            found = {
                row.id
                for row in self.db.scalars(select(CareerPath).where(CareerPath.id.in_(unique_ids))).all()
            }
            missing = [str(item) for item in unique_ids if item not in found]
            if missing:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown career path")
        existing = self.db.scalars(select(UserCareerInterest).where(UserCareerInterest.user_id == user.id)).all()
        for row in existing:
            self.db.delete(row)
        self.db.flush()
        for path_id in unique_ids:
            self.db.add(UserCareerInterest(user_id=user.id, career_path_id=path_id))
        self.db.commit()
        return self.get_interests(user)

    def save(self, user: User, opportunity_id: UUID) -> OpportunitySavePublic:
        opportunity = self._require_public(opportunity_id)
        row = self.db.scalar(
            select(OpportunitySave).where(
                OpportunitySave.user_id == user.id,
                OpportunitySave.opportunity_id == opportunity.id,
            )
        )
        if row is None:
            row = OpportunitySave(
                user_id=user.id,
                opportunity_id=opportunity.id,
                state=OpportunitySaveState.SAVED,
            )
            self.db.add(row)
        elif row.state != OpportunitySaveState.APPLIED:
            row.state = OpportunitySaveState.SAVED
        self.db.commit()
        self.db.refresh(row)
        return self._public(row, self.opportunities._get(opportunity.id))

    def mark_applied(self, user: User, opportunity_id: UUID) -> OpportunitySavePublic:
        opportunity = self._require_public(opportunity_id)
        row = self.db.scalar(
            select(OpportunitySave).where(
                OpportunitySave.user_id == user.id,
                OpportunitySave.opportunity_id == opportunity.id,
            )
        )
        if row is None:
            row = OpportunitySave(
                user_id=user.id,
                opportunity_id=opportunity.id,
                state=OpportunitySaveState.APPLIED,
            )
            self.db.add(row)
        else:
            row.state = OpportunitySaveState.APPLIED
        self.db.commit()
        self.db.refresh(row)
        return self._public(row, self.opportunities._get(opportunity.id))

    def unsave(self, user: User, opportunity_id: UUID) -> None:
        row = self.db.scalar(
            select(OpportunitySave).where(
                OpportunitySave.user_id == user.id,
                OpportunitySave.opportunity_id == opportunity_id,
            )
        )
        if row is None:
            return
        self.db.delete(row)
        self.db.commit()

    def list_saved(self, user: User, *, bucket: str = "saved") -> OpportunitySaveList:
        rows = self.db.scalars(
            select(OpportunitySave)
            .options(
                selectinload(OpportunitySave.opportunity).selectinload(Opportunity.career_path_links).selectinload(OpportunityCareerPath.career_path),
                selectinload(OpportunitySave.opportunity).selectinload(Opportunity.skill_links).selectinload(OpportunitySkill.skill),
                selectinload(OpportunitySave.opportunity).selectinload(Opportunity.source),
            )
            .where(OpportunitySave.user_id == user.id)
            .order_by(OpportunitySave.updated_at.desc())
        ).all()
        items: list[OpportunitySavePublic] = []
        for row in rows:
            opportunity = row.opportunity
            if not opportunity:
                continue
            public = self._public(row, opportunity)
            if bucket == "applied" and public.state != "applied":
                continue
            if bucket == "closed" and not public.closed:
                continue
            if bucket == "saved" and public.closed:
                continue
            if bucket == "saved" and public.state == "applied":
                continue
            items.append(public)
        return OpportunitySaveList(items=items, total=len(items))

    def _require_public(self, opportunity_id: UUID) -> Opportunity:
        opportunity = self.db.get(Opportunity, opportunity_id)
        if not opportunity or opportunity.status != OpportunityStatus.PUBLISHED:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
        return opportunity

    def _public(self, row: OpportunitySave, opportunity: Opportunity) -> OpportunitySavePublic:
        closed = opportunity.status != OpportunityStatus.PUBLISHED
        deadline = opportunity.deadline
        if deadline is not None:
            due = deadline if deadline.tzinfo else deadline.replace(tzinfo=UTC)
            if due < self._utcnow():
                closed = True
        card = self.opportunities._card(opportunity)
        return OpportunitySavePublic(
            id=row.id,
            opportunity_id=opportunity.id,
            state=row.state.value,
            closed=closed,
            created_at=row.created_at,
            opportunity=card,
        )


def match_score(opportunity: Opportunity, interest_path_ids: set[UUID]) -> float | None:
    if not interest_path_ids:
        return None
    overlap = sum(1 for link in opportunity.career_path_links if link.career_path_id in interest_path_ids)
    if overlap == 0:
        return 0.0
    return float(min(100, overlap * 40 + (20 if opportunity.featured else 0)))
