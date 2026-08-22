from fastapi import APIRouter, Depends, Query

from app.api.deps import get_admin_service, get_auth_service, get_self_paced_service, require_admin, require_catalog_ops
from app.models.user import User
from app.schemas.admin import (
    AdminCohortDetail,
    AdminOverview,
    AdminPaymentRow,
    AdminUserRow,
    InviteInstructorRequest,
    InviteInstructorResponse,
)
from app.schemas.self_paced import AdminCourseAnalytics, AdminCourseRow
from app.services.admin import AdminService
from app.services.auth import AuthService
from app.services.self_paced import SelfPacedService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview", response_model=AdminOverview)
def admin_overview(
    _: User = Depends(require_admin),
    admin: AdminService = Depends(get_admin_service),
) -> AdminOverview:
    return admin.overview()


@router.get("/users", response_model=list[AdminUserRow])
def admin_users(
    _: User = Depends(require_admin),
    admin: AdminService = Depends(get_admin_service),
    limit: int = Query(default=200, ge=1, le=500),
) -> list[AdminUserRow]:
    return admin.list_users(limit=limit)


@router.get("/payments", response_model=list[AdminPaymentRow])
def admin_payments(
    _: User = Depends(require_admin),
    admin: AdminService = Depends(get_admin_service),
    limit: int = Query(default=200, ge=1, le=500),
) -> list[AdminPaymentRow]:
    return admin.list_payments(limit=limit)


@router.get("/courses", response_model=list[AdminCourseRow])
def admin_courses(
    _: User = Depends(require_catalog_ops),
    lms: SelfPacedService = Depends(get_self_paced_service),
) -> list[AdminCourseRow]:
    return lms.list_admin_courses()


@router.get("/courses/{slug}/analytics", response_model=AdminCourseAnalytics)
def admin_course_analytics(
    slug: str,
    _: User = Depends(require_admin),
    lms: SelfPacedService = Depends(get_self_paced_service),
) -> AdminCourseAnalytics:
    return lms.course_analytics(slug)


@router.get("/cohorts/{slug}", response_model=AdminCohortDetail)
def admin_cohort(
    slug: str,
    _: User = Depends(require_admin),
    admin: AdminService = Depends(get_admin_service),
) -> AdminCohortDetail:
    return admin.cohort_detail(slug)


@router.post("/instructors", response_model=InviteInstructorResponse)
def invite_instructor(
    payload: InviteInstructorRequest,
    _: User = Depends(require_admin),
    auth: AuthService = Depends(get_auth_service),
    admin: AdminService = Depends(get_admin_service),
) -> InviteInstructorResponse:
    user, resent = auth.invite_instructor(email=payload.email, full_name=payload.full_name)
    admin.add_instructor_to_featured_cohort(user)
    message = (
        f"Invite resent to {user.email}."
        if resent
        else f"Invite sent to {user.email}. They have 7 days to set a password."
    )
    return InviteInstructorResponse(
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        resent=resent,
        message=message,
    )


@router.post("/operations", response_model=InviteInstructorResponse)
def invite_operations(
    payload: InviteInstructorRequest,
    _: User = Depends(require_admin),
    auth: AuthService = Depends(get_auth_service),
) -> InviteInstructorResponse:
    user, resent = auth.invite_operations(email=payload.email, full_name=payload.full_name)
    message = (
        f"Invite resent to {user.email}."
        if resent
        else f"Invite sent to {user.email}. They have 7 days to set a password."
    )
    return InviteInstructorResponse(
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        resent=resent,
        message=message,
    )


@router.post("/editors", response_model=InviteInstructorResponse)
def invite_editor(
    payload: InviteInstructorRequest,
    _: User = Depends(require_admin),
    auth: AuthService = Depends(get_auth_service),
) -> InviteInstructorResponse:
    user, resent = auth.invite_editor(email=payload.email, full_name=payload.full_name)
    message = (
        f"Invite resent to {user.email}."
        if resent
        else f"Invite sent to {user.email}. They have 7 days to set a password."
    )
    return InviteInstructorResponse(
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        resent=resent,
        message=message,
    )


@router.post("/authors", response_model=InviteInstructorResponse)
def invite_author(
    payload: InviteInstructorRequest,
    _: User = Depends(require_admin),
    auth: AuthService = Depends(get_auth_service),
) -> InviteInstructorResponse:
    user, resent = auth.invite_author(email=payload.email, full_name=payload.full_name)
    message = (
        f"Invite resent to {user.email}."
        if resent
        else f"Invite sent to {user.email}. They have 7 days to set a password."
    )
    return InviteInstructorResponse(
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        resent=resent,
        message=message,
    )
