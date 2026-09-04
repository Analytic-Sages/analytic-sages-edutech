"""Public, partner, and admin Referral Partner Program APIs."""

from __future__ import annotations

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional, get_db, require_admin
from app.core.config import Settings, get_settings
from app.core.referrals import PartnerPayoutStatus, ReferralConversionStatus, ReferralPartnerStatus
from app.core.roles import UserRole
from app.models.classroom import Cohort
from app.models.course import Course
from app.models.referral import PartnerPayoutRequest, ReferralConversion, ReferralPartner
from app.models.user import User
from app.schemas.referrals import (
    AdminConversionRow,
    AdminPartnerPatch,
    AdminPayoutPatch,
    AdminReferralOverview,
    LeaderboardEntry,
    LeaderboardResponse,
    PartnerApplyRequest,
    PartnerConversionRow,
    PartnerDashboard,
    PartnerPayoutCreate,
    PartnerPayoutRow,
    PartnerPublic,
    ReferralTrackRequest,
    ReferralTrackResponse,
    ReleaseCommissionsResponse,
)
from app.services.referrals import (
    VISITOR_COOKIE,
    ReferralAttributionService,
    ReferralCommissionService,
    ReferralDashboardService,
    ReferralPartnerService,
    ReferralPayoutService,
    referral_money,
)

router = APIRouter(tags=["referrals"])


def _partners(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return ReferralPartnerService(db, settings)


def _attribution(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return ReferralAttributionService(db, settings)


def _dashboard(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return ReferralDashboardService(db, settings)


def _payouts(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return ReferralPayoutService(db, settings)


def _require_partner(
    user: User = Depends(get_current_user),
    partners: ReferralPartnerService = Depends(_partners),
) -> ReferralPartner:
    partner = partners.get_by_user(user.id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral Partner profile not found",
        )
    return partner


def _privacy_name(full_name: str | None, email: str) -> str:
    if full_name and full_name.strip():
        parts = full_name.strip().split()
        if len(parts) == 1:
            return parts[0]
        return f"{parts[0]} {parts[-1][0]}."
    return email.split("@")[0]


def _programme_title(db: Session, conversion: ReferralConversion) -> str:
    if conversion.cohort_id:
        cohort = db.get(Cohort, conversion.cohort_id)
        if cohort:
            return cohort.name
    if conversion.course_id:
        course = db.get(Course, conversion.course_id)
        if course:
            return course.title
    return "Programme"


@router.post("/referrals/track", response_model=ReferralTrackResponse)
def track_referral(
    payload: ReferralTrackRequest,
    request: Request,
    response: Response,
    attribution: ReferralAttributionService = Depends(_attribution),
    settings: Settings = Depends(get_settings),
) -> ReferralTrackResponse:
    visitor_id = payload.anonymous_visitor_id or request.cookies.get(VISITOR_COOKIE)
    if not visitor_id:
        visitor_id = uuid.uuid4().hex
    ok, redirect_path = attribution.track_click(
        code=payload.code,
        anonymous_visitor_id=visitor_id,
        landing_path=payload.landing_path,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        destination=payload.destination,
    )
    response.set_cookie(
        key=VISITOR_COOKIE,
        value=visitor_id,
        max_age=60 * 60 * 24 * settings.referral_attribution_days,
        httponly=True,
        secure=settings.cookie_secure or settings.is_production,
        samesite=settings.refresh_cookie_samesite,
        path="/",
        domain=settings.cookie_domain,
    )
    return ReferralTrackResponse(ok=ok, redirect_path=redirect_path, anonymous_visitor_id=visitor_id)


@router.get("/referrals/leaderboard", response_model=LeaderboardResponse)
def public_leaderboard(
    period: str = Query(default="all", pattern="^(all|monthly)$"),
    settings: Settings = Depends(get_settings),
    dashboard: ReferralDashboardService = Depends(_dashboard),
    current_user: User | None = Depends(get_current_user_optional),
) -> LeaderboardResponse:
    if not settings.partners_public and (
        current_user is None or current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    entries = [
        LeaderboardEntry(**row) for row in dashboard.leaderboard(period=period, limit=25)
    ]
    return LeaderboardResponse(period=period, entries=entries)


@router.post("/partners/apply", response_model=PartnerPublic)
def apply_partner(
    payload: PartnerApplyRequest,
    user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    partners: ReferralPartnerService = Depends(_partners),
) -> PartnerPublic:
    if not settings.partners_public and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    partner = partners.apply(
        user=user,
        display_name=payload.display_name,
        social_handle=payload.social_handle,
        promotion_channels=payload.promotion_channels,
        terms_accepted=payload.terms_accepted,
    )
    return PartnerPublic.model_validate(partner)


@router.get("/partner/me", response_model=PartnerPublic | None)
def my_partner_profile(
    user: User = Depends(get_current_user),
    partners: ReferralPartnerService = Depends(_partners),
) -> PartnerPublic | None:
    partner = partners.get_by_user(user.id)
    return PartnerPublic.model_validate(partner) if partner else None


@router.get("/partner/dashboard", response_model=PartnerDashboard)
def partner_dashboard(
    partner: ReferralPartner = Depends(_require_partner),
    dashboard: ReferralDashboardService = Depends(_dashboard),
    settings: Settings = Depends(get_settings),
) -> PartnerDashboard:
    data = dashboard.partner_overview(partner)
    link = None
    if partner.referral_code:
        link = f"{settings.frontend_url.rstrip('/')}/ref/{partner.referral_code}"
    return PartnerDashboard(**data, referral_link=link)


@router.get("/partner/conversions", response_model=list[PartnerConversionRow])
def partner_conversions(
    partner: ReferralPartner = Depends(_require_partner),
    db: Session = Depends(get_db),
) -> list[PartnerConversionRow]:
    rows = list(
        db.scalars(
            select(ReferralConversion)
            .where(ReferralConversion.partner_id == partner.id)
            .order_by(ReferralConversion.created_at.desc())
            .limit(100)
        ).all()
    )
    out: list[PartnerConversionRow] = []
    for row in rows:
        user = db.get(User, row.referred_user_id)
        out.append(
            PartnerConversionRow(
                id=row.id,
                programme=_programme_title(db, row),
                learner_label=_privacy_name(
                    user.full_name if user else None,
                    user.email if user else "learner",
                ),
                eligible_amount=row.eligible_amount,
                commission_amount=row.commission_amount,
                currency=row.currency,
                status=row.status,
                created_at=row.created_at,
            )
        )
    return out


@router.get("/partner/payouts", response_model=list[PartnerPayoutRow])
def partner_payouts(
    partner: ReferralPartner = Depends(_require_partner),
    db: Session = Depends(get_db),
) -> list[PartnerPayoutRow]:
    rows = list(
        db.scalars(
            select(PartnerPayoutRequest)
            .where(PartnerPayoutRequest.partner_id == partner.id)
            .order_by(PartnerPayoutRequest.requested_at.desc())
            .limit(50)
        ).all()
    )
    return [PartnerPayoutRow.model_validate(r) for r in rows]


@router.post("/partner/payouts", response_model=PartnerPayoutRow)
def request_payout(
    payload: PartnerPayoutCreate,
    partner: ReferralPartner = Depends(_require_partner),
    payouts: ReferralPayoutService = Depends(_payouts),
) -> PartnerPayoutRow:
    payout = payouts.request_payout(
        partner=partner,
        amount=referral_money(payload.amount),
        currency=payload.currency,
        payment_details_reference=payload.payment_details_reference,
    )
    return PartnerPayoutRow.model_validate(payout)


@router.get("/admin/referrals/overview", response_model=AdminReferralOverview)
def admin_overview(
    _: User = Depends(require_admin),
    dashboard: ReferralDashboardService = Depends(_dashboard),
) -> AdminReferralOverview:
    return AdminReferralOverview(**dashboard.admin_overview())


@router.get("/admin/referrals/partners", response_model=list[PartnerPublic])
def admin_list_partners(
    _: User = Depends(require_admin),
    partners: ReferralPartnerService = Depends(_partners),
    status_filter: ReferralPartnerStatus | None = Query(default=None, alias="status"),
) -> list[PartnerPublic]:
    return [PartnerPublic.model_validate(p) for p in partners.list_partners(status_filter=status_filter)]


@router.patch("/admin/referrals/partners/{partner_id}", response_model=PartnerPublic)
def admin_patch_partner(
    partner_id: UUID,
    payload: AdminPartnerPatch,
    admin: User = Depends(require_admin),
    partners: ReferralPartnerService = Depends(_partners),
) -> PartnerPublic:
    if payload.regenerate_code and not payload.status:
        partner = partners.regenerate_code(partner_id=partner_id, actor=admin)
        return PartnerPublic.model_validate(partner)
    if not payload.status:
        raise HTTPException(status_code=400, detail="status or regenerate_code required")
    partner = partners.set_status(
        partner_id=partner_id,
        status_value=payload.status,
        actor=admin,
        note=payload.note,
        regenerate_code=payload.regenerate_code,
    )
    return PartnerPublic.model_validate(partner)


@router.get("/admin/referrals/conversions", response_model=list[AdminConversionRow])
def admin_conversions(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    status_filter: ReferralConversionStatus | None = Query(default=None, alias="status"),
) -> list[AdminConversionRow]:
    stmt = select(ReferralConversion).order_by(ReferralConversion.created_at.desc()).limit(200)
    if status_filter:
        stmt = stmt.where(ReferralConversion.status == status_filter)
    rows = list(db.scalars(stmt).all())
    out: list[AdminConversionRow] = []
    for row in rows:
        partner = db.get(ReferralPartner, row.partner_id)
        user = db.get(User, row.referred_user_id)
        out.append(
            AdminConversionRow(
                id=row.id,
                partner_name=partner.display_name if partner else "—",
                learner_email=user.email if user else "—",
                programme=_programme_title(db, row),
                payment_id=row.payment_id,
                eligible_amount=row.eligible_amount,
                commission_amount=row.commission_amount,
                currency=row.currency,
                status=row.status,
                created_at=row.created_at,
            )
        )
    return out


@router.get("/admin/referrals/payouts", response_model=list[PartnerPayoutRow])
def admin_payouts(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    status_filter: PartnerPayoutStatus | None = Query(default=None, alias="status"),
) -> list[PartnerPayoutRow]:
    stmt = select(PartnerPayoutRequest).order_by(PartnerPayoutRequest.requested_at.desc()).limit(100)
    if status_filter:
        stmt = stmt.where(PartnerPayoutRequest.status == status_filter)
    return [PartnerPayoutRow.model_validate(r) for r in db.scalars(stmt).all()]


@router.patch("/admin/referrals/payouts/{payout_id}", response_model=PartnerPayoutRow)
def admin_patch_payout(
    payout_id: UUID,
    payload: AdminPayoutPatch,
    admin: User = Depends(require_admin),
    payouts: ReferralPayoutService = Depends(_payouts),
) -> PartnerPayoutRow:
    payout = payouts.update_status(
        payout_id=payout_id,
        status_value=payload.status,
        actor=admin,
        note=payload.note,
    )
    return PartnerPayoutRow.model_validate(payout)


@router.get("/admin/referrals/review-queue", response_model=list[AdminConversionRow])
def admin_review_queue(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AdminConversionRow]:
    rows = list(
        db.scalars(
            select(ReferralConversion)
            .where(ReferralConversion.status == ReferralConversionStatus.REVIEW_REQUIRED)
            .order_by(ReferralConversion.created_at.desc())
            .limit(100)
        ).all()
    )
    out: list[AdminConversionRow] = []
    for row in rows:
        partner = db.get(ReferralPartner, row.partner_id)
        user = db.get(User, row.referred_user_id)
        out.append(
            AdminConversionRow(
                id=row.id,
                partner_name=partner.display_name if partner else "—",
                learner_email=user.email if user else "—",
                programme=_programme_title(db, row),
                payment_id=row.payment_id,
                eligible_amount=row.eligible_amount,
                commission_amount=row.commission_amount,
                currency=row.currency,
                status=row.status,
                created_at=row.created_at,
            )
        )
    return out


@router.post("/internal/referrals/release-commissions", response_model=ReleaseCommissionsResponse)
def release_commissions(
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
    x_referral_release_token: str | None = Header(default=None),
) -> ReleaseCommissionsResponse:
    token = settings.referral_release_token
    if not token or x_referral_release_token != token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    released = ReferralCommissionService(db, settings).release_held_commissions()
    return ReleaseCommissionsResponse(released=released)
