from __future__ import annotations

import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.classroom import Cohort
from app.models.user import User
from app.models.waitlist import CohortWaitlistEntry
from app.schemas.waitlist import (
    REQUIRED_WAITLIST_FIELDS,
    AdminWaitlistResponse,
    AdminWaitlistRow,
    WaitlistEntryPublic,
    WaitlistJoinRequest,
    WaitlistStatusPublic,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WaitlistService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_cohort(self, cohort_id: UUID) -> Cohort:
        cohort = self.db.get(Cohort, cohort_id)
        if not cohort:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")
        return cohort

    def _get_cohort_by_slug(self, slug: str) -> Cohort:
        cohort = self.db.scalar(select(Cohort).where(Cohort.slug == slug))
        if not cohort:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")
        return cohort

    def is_waitlist_open(self, cohort: Cohort) -> bool:
        """Waitlist mode is on when explicitly flagged, or once registration closes.

        A cohort whose programme has already started (or whose registration deadline
        has passed) can no longer be bought, so prospective students join the waitlist
        for the next intake instead.
        """
        settings = cohort.enrollment_settings or {}
        if "waitlist_open" in settings:
            return bool(settings.get("waitlist_open"))
        now = _utcnow()
        started = cohort.starts_at is not None and cohort.starts_at <= now
        deadline_passed = (
            cohort.registration_deadline is not None and cohort.registration_deadline <= now
        )
        return started or deadline_passed

    def missing_fields(self, user: User) -> list[str]:
        missing: list[str] = []
        for field in REQUIRED_WAITLIST_FIELDS:
            value = getattr(user, field, None)
            if value is None or not str(value).strip():
                missing.append(field)
        return missing

    def _entry_public(self, entry: CohortWaitlistEntry) -> WaitlistEntryPublic:
        return WaitlistEntryPublic(
            id=entry.id,
            cohort_id=entry.cohort_id,
            created_at=entry.created_at,
        )

    def _find_entry(self, cohort_id: UUID, user_id: UUID) -> CohortWaitlistEntry | None:
        return self.db.scalar(
            select(CohortWaitlistEntry).where(
                CohortWaitlistEntry.cohort_id == cohort_id,
                CohortWaitlistEntry.user_id == user_id,
            )
        )

    def status(self, user: User, cohort_id: UUID) -> WaitlistStatusPublic:
        cohort = self._get_cohort(cohort_id)
        entry = self._find_entry(cohort_id, user.id)
        return WaitlistStatusPublic(
            is_open=self.is_waitlist_open(cohort),
            is_on_waitlist=entry is not None,
            missing_fields=self.missing_fields(user),
            entry=self._entry_public(entry) if entry else None,
        )

    def join(self, user: User, cohort_id: UUID, payload: WaitlistJoinRequest) -> WaitlistEntryPublic:
        cohort = self._get_cohort(cohort_id)
        missing = self.missing_fields(user)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Complete your profile before joining the waitlist.",
                    "missing_fields": missing,
                },
            )

        entry = self._find_entry(cohort_id, user.id)
        if entry is None:
            entry = CohortWaitlistEntry(
                id=uuid.uuid4(),
                cohort_id=cohort.id,
                user_id=user.id,
                note=(payload.note or None),
            )
            self.db.add(entry)
        elif payload.note is not None:
            entry.note = payload.note or None
        self.db.commit()
        self.db.refresh(entry)
        return self._entry_public(entry)

    # ---------- admin ----------

    def admin_list(self, slug: str) -> AdminWaitlistResponse:
        cohort = self._get_cohort_by_slug(slug)
        entries = list(
            self.db.scalars(
                select(CohortWaitlistEntry)
                .options(selectinload(CohortWaitlistEntry.user))
                .where(CohortWaitlistEntry.cohort_id == cohort.id)
                .order_by(CohortWaitlistEntry.created_at.desc())
            ).all()
        )
        rows = [
            AdminWaitlistRow(
                user_id=entry.user_id,
                full_name=entry.user.full_name if entry.user else None,
                email=entry.user.email if entry.user else "",
                phone_number=entry.user.phone_number if entry.user else None,
                phone_country_code=entry.user.phone_country_code if entry.user else None,
                country_of_residence=entry.user.country_of_residence if entry.user else None,
                discord_username=entry.user.discord_username if entry.user else None,
                telegram_username=entry.user.telegram_username if entry.user else None,
                note=entry.note,
                created_at=entry.created_at,
            )
            for entry in entries
        ]
        return AdminWaitlistResponse(
            cohort_id=cohort.id,
            cohort_slug=cohort.slug,
            cohort_name=cohort.name,
            is_open=self.is_waitlist_open(cohort),
            count=len(rows),
            entries=rows,
        )