from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import (
    CurrentUser,
    get_waitlist_service,
    require_admin,
)
from app.models.user import User
from app.schemas.waitlist import (
    AdminWaitlistResponse,
    WaitlistEntryPublic,
    WaitlistJoinRequest,
    WaitlistStatusPublic,
)
from app.services.waitlist import WaitlistService

router = APIRouter(tags=["waitlist"])


@router.get("/cohorts/{cohort_id}/waitlist/me", response_model=WaitlistStatusPublic)
def my_waitlist_status(
    cohort_id: UUID,
    current_user: CurrentUser,
    waitlist: WaitlistService = Depends(get_waitlist_service),
) -> WaitlistStatusPublic:
    return waitlist.status(current_user, cohort_id)


@router.post("/cohorts/{cohort_id}/waitlist", response_model=WaitlistEntryPublic)
def join_waitlist(
    cohort_id: UUID,
    payload: WaitlistJoinRequest,
    current_user: CurrentUser,
    waitlist: WaitlistService = Depends(get_waitlist_service),
) -> WaitlistEntryPublic:
    return waitlist.join(current_user, cohort_id, payload)


@router.get("/admin/cohorts/{slug}/waitlist", response_model=AdminWaitlistResponse)
def admin_cohort_waitlist(
    slug: str,
    _: User = Depends(require_admin),
    waitlist: WaitlistService = Depends(get_waitlist_service),
) -> AdminWaitlistResponse:
    return waitlist.admin_list(slug)