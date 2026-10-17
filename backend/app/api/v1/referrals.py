"""Public, partner, and admin Referral Partner Program APIs."""

from __future__ import annotations

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional, get_db, require_admin
from app.core.config import Settings, get_settings
from app.core.referrals import (
    PartnerPayoutStatus,
    ReferralConversionStatus,
    ReferralFraudStatus,
    ReferralPartnerStatus,
)
from app.core.roles import UserRole
from app.models.classroom import Cohort
from app.models.course import Course
from app.models.referral import PartnerPayoutRequest, ReferralConversion, ReferralLink, ReferralPartner, ReferralPartnerApplication, ReferralPartnerCohort
from app.models.user import User
from app.schemas.referrals import (
    AdminAttributionOverride,
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
from app.schemas.referral_onboarding import (
    PartnerOnboardingComplete,
    ReferralLinkCreate,
    ReferralLinkPatch,
    ReferralLinkPublic,
    ReferralPartnerApplicationCreate,
    ReferralPartnerApplicationPatch,
    ReferralPartnerApplicationPublic,
    ReferralPartnerCohortCreate,
    ReferralPartnerCohortPatch,
    ReferralPartnerCohortPublic,
)
from app.services.referral_onboarding import ReferralOnboardingService
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


def _onboarding(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return ReferralOnboardingService(db, settings)


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
    if not (user.email or user.phone_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add an email address or WhatsApp number to your account before applying.",
        )
    if not user.telegram_username or not user.telegram_username.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add your Telegram handle to your account before applying.",
        )
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


def _admin_conversion_row(db: Session, row: ReferralConversion) -> AdminConversionRow:
    partner = db.get(ReferralPartner, row.partner_id)
    user = db.get(User, row.referred_user_id)
    return AdminConversionRow(
        id=row.id,
        partner_name=partner.display_name if partner else "—",
        learner_email=user.email if user else "—",
        programme=_programme_title(db, row),
        payment_id=row.payment_id,
        eligible_amount=row.eligible_amount,
        commission_amount=row.commission_amount,
        currency=row.currency,
        status=row.status,
        fraud_status=row.fraud_status,
        created_at=row.created_at,
        reporting_usd_equivalent=row.reporting_usd_equivalent,
    )


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
                reporting_usd_equivalent=row.reporting_usd_equivalent,
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




@router.get("/partners/eligible-courses")
def referral_eligible_courses(
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> list[dict]:
    if not settings.partners_public and (current_user is None or current_user.role != UserRole.ADMIN):
        raise HTTPException(status_code=404, detail="Not found")
    courses = db.scalars(
        select(Course).where(
            Course.published.is_(True),
            Course.referral_commission_eligible.is_(True),
            Course.is_free.is_(False),
        ).order_by(Course.title.asc())
    ).all()
    return [{"id": str(course.id), "slug": course.slug, "title": course.title} for course in courses]


@router.post("/partners/applications", response_model=ReferralPartnerApplicationPublic, status_code=201)
def submit_referral_application(
    payload: ReferralPartnerApplicationCreate,
    settings: Settings = Depends(get_settings),
    current_user: User | None = Depends(get_current_user_optional),
    service: ReferralOnboardingService = Depends(_onboarding),
) -> ReferralPartnerApplicationPublic:
    if not settings.partners_public and (current_user is None or current_user.role != UserRole.ADMIN):
        raise HTTPException(status_code=404, detail="Not found")
    application = service.submit_application(payload=payload, user=current_user, actor_id=current_user.id if current_user else None)
    return ReferralPartnerApplicationPublic.model_validate(application)





@router.get("/partner/application/me", response_model=ReferralPartnerApplicationPublic | None)
def my_referral_application(
    user: User = Depends(get_current_user),
    service: ReferralOnboardingService = Depends(_onboarding),
) -> ReferralPartnerApplicationPublic | None:
    if not user.email_verified:
        return None
    from app.services.referral_onboarding import normalize_email
    application = service.db.scalar(
        select(ReferralPartnerApplication).where(
            ReferralPartnerApplication.email_normalized == normalize_email(user.email)
        )
    )
    if application and application.user_id and application.user_id != user.id:
        return None
    return ReferralPartnerApplicationPublic.model_validate(application) if application else None


@router.post("/partner/onboarding/claim", response_model=ReferralPartnerApplicationPublic)
def claim_referral_application(
    user: User = Depends(get_current_user),
    service: ReferralOnboardingService = Depends(_onboarding),
) -> ReferralPartnerApplicationPublic:
    application = service.claim_approved_application(user=user)
    return ReferralPartnerApplicationPublic.model_validate(application)


@router.post("/partner/onboarding/complete", response_model=PartnerPublic)
def complete_referral_onboarding(
    payload: PartnerOnboardingComplete,
    user: User = Depends(get_current_user),
    partner: ReferralPartner = Depends(_require_partner),
    service: ReferralOnboardingService = Depends(_onboarding),
) -> PartnerPublic:
    updated = service.complete_onboarding(partner=partner, payload=payload, actor=user)
    return PartnerPublic.model_validate(updated)


@router.get("/partner/link-targets")
def partner_referral_link_targets(
    _: ReferralPartner = Depends(_require_partner),
    db: Session = Depends(get_db),
) -> dict:
    courses = db.scalars(
        select(Course).where(
            Course.published.is_(True),
            Course.referral_commission_eligible.is_(True),
            Course.is_free.is_(False),
        ).order_by(Course.title.asc())
    ).all()
    programmes = db.scalars(
        select(Cohort).where(
            Cohort.referral_commission_eligible.is_(True),
            Cohort.price > 0,
            Cohort.status.in_(["open", "active"]),
        ).order_by(Cohort.name.asc())
    ).all()
    return {
        "courses": [{"id": str(row.id), "slug": row.slug, "title": row.title} for row in courses],
        "programmes": [{"id": str(row.id), "slug": row.slug, "title": row.name} for row in programmes],
    }


@router.get("/partner/links", response_model=list[ReferralLinkPublic])
def partner_referral_links(
    partner: ReferralPartner = Depends(_require_partner),
    service: ReferralOnboardingService = Depends(_onboarding),
) -> list[ReferralLinkPublic]:
    return [ReferralLinkPublic(**row) for row in service.list_links(partner=partner)]


@router.post("/partner/links", response_model=ReferralLinkPublic, status_code=201)
def create_partner_referral_link(
    payload: ReferralLinkCreate,
    user: User = Depends(get_current_user),
    partner: ReferralPartner = Depends(_require_partner),
    service: ReferralOnboardingService = Depends(_onboarding),
) -> ReferralLinkPublic:
    link = service.create_link(partner=partner, payload=payload, actor=user)
    rows = service.list_links(partner=partner)
    item = next((row for row in rows if row["id"] == link.id), None)
    if not item:
        raise HTTPException(status_code=500, detail="Created link could not be loaded.")
    return ReferralLinkPublic(**item)


@router.patch("/partner/links/{link_id}", response_model=ReferralLinkPublic)
def patch_partner_referral_link(
    link_id: UUID,
    payload: ReferralLinkPatch,
    user: User = Depends(get_current_user),
    partner: ReferralPartner = Depends(_require_partner),
    service: ReferralOnboardingService = Depends(_onboarding),
) -> ReferralLinkPublic:
    if payload.status not in {"inactive", "revoked"}:
        raise HTTPException(status_code=400, detail="Partners may only pause or revoke their own links.")
    service.patch_link(link_id=link_id, actor=user, partner=partner, status_value=payload.status, reason=payload.revocation_reason)
    rows = service.list_links(partner=partner)
    item = next((row for row in rows if row["id"] == link_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Referral link not found.")
    return ReferralLinkPublic(**item)


@router.get("/admin/referrals/applications", response_model=list[ReferralPartnerApplicationPublic])
def admin_referral_applications(
    _: User = Depends(require_admin),
    service: ReferralOnboardingService = Depends(_onboarding),
    status_filter: str | None = Query(default=None, alias="status"),
) -> list[ReferralPartnerApplicationPublic]:
    return [ReferralPartnerApplicationPublic.model_validate(row) for row in service.list_applications(status_filter=status_filter)]


@router.patch("/admin/referrals/applications/{application_id}", response_model=ReferralPartnerApplicationPublic)
def admin_patch_referral_application(
    application_id: UUID,
    payload: ReferralPartnerApplicationPatch,
    admin: User = Depends(require_admin),
    service: ReferralOnboardingService = Depends(_onboarding),
) -> ReferralPartnerApplicationPublic:
    application = service.patch_application(application_id=application_id, payload=payload, actor=admin)
    return ReferralPartnerApplicationPublic.model_validate(application)


@router.get("/admin/referrals/cohorts", response_model=list[ReferralPartnerCohortPublic])
def admin_referral_cohorts(
    _: User = Depends(require_admin),
    service: ReferralOnboardingService = Depends(_onboarding),
) -> list[ReferralPartnerCohortPublic]:
    return [ReferralPartnerCohortPublic(**row) for row in service.list_cohorts()]


@router.post("/admin/referrals/cohorts", response_model=ReferralPartnerCohortPublic, status_code=201)
def admin_create_referral_cohort(
    payload: ReferralPartnerCohortCreate,
    admin: User = Depends(require_admin),
    service: ReferralOnboardingService = Depends(_onboarding),
) -> ReferralPartnerCohortPublic:
    row = service.create_cohort(name=payload.name, capacity=payload.capacity, is_active=payload.is_active, actor=admin)
    return ReferralPartnerCohortPublic(**row)


@router.patch("/admin/referrals/cohorts/{cohort_id}", response_model=ReferralPartnerCohortPublic)
def admin_patch_referral_cohort(
    cohort_id: UUID,
    payload: ReferralPartnerCohortPatch,
    admin: User = Depends(require_admin),
    service: ReferralOnboardingService = Depends(_onboarding),
) -> ReferralPartnerCohortPublic:
    row = service.patch_cohort(cohort_id=cohort_id, capacity=payload.capacity, is_active=payload.is_active, actor=admin)
    return ReferralPartnerCohortPublic(**row)


@router.get("/admin/referrals/links", response_model=list[ReferralLinkPublic])
def admin_list_referral_links(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    service: ReferralOnboardingService = Depends(_onboarding),
    partner_id: UUID | None = None,
) -> list[ReferralLinkPublic]:
    if partner_id:
        partner = db.get(ReferralPartner, partner_id)
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found.")
        rows = service.list_links(partner=partner)
    else:
        rows = []
        for partner in db.scalars(select(ReferralPartner).order_by(ReferralPartner.created_at.desc()).limit(500)).all():
            rows.extend(service.list_links(partner=partner))
    return [ReferralLinkPublic(**row) for row in rows]


@router.patch("/admin/referrals/links/{link_id}", response_model=ReferralLinkPublic)
def admin_patch_referral_link(
    link_id: UUID,
    payload: ReferralLinkPatch,
    admin: User = Depends(require_admin),
    service: ReferralOnboardingService = Depends(_onboarding),
) -> ReferralLinkPublic:
    if payload.status is None:
        raise HTTPException(status_code=400, detail="status is required.")
    service.patch_link(link_id=link_id, actor=admin, status_value=payload.status, reason=payload.revocation_reason)
    link = service.db.get(ReferralLink, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Referral link not found.")
    partner = service.db.get(ReferralPartner, link.partner_id)
    rows = service.list_links(partner=partner) if partner else []
    item = next((row for row in rows if row["id"] == link_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Referral link not found.")
    return ReferralLinkPublic(**item)


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
    db: Session = Depends(get_db),
) -> PartnerPublic:
    if payload.status == ReferralPartnerStatus.ACTIVE:
        existing_partner = db.get(ReferralPartner, partner_id)
        if not existing_partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        # New applicants must complete the onboarding checklist before activation.
        # Preserve admin reactivation for established legacy partners that were
        # active before this onboarding workflow was introduced.
        if (
            existing_partner.status == ReferralPartnerStatus.PENDING
            and existing_partner.onboarding_completed_at is None
        ):
            raise HTTPException(
                status_code=409,
                detail="Complete partner onboarding before activation.",
            )
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
    return [_admin_conversion_row(db, row) for row in db.scalars(stmt).all()]


@router.post("/admin/referrals/attributions/override")
def admin_override_attribution(
    payload: AdminAttributionOverride,
    admin: User = Depends(require_admin),
    attribution: ReferralAttributionService = Depends(_attribution),
) -> dict:
    attr = attribution.admin_override_lock(
        referred_user_id=payload.referred_user_id,
        partner_id=payload.partner_id,
        actor=admin,
        note=payload.note,
    )
    return {
        "ok": True,
        "attribution_id": str(attr.id),
        "partner_id": str(attr.partner_id),
        "referred_user_id": str(attr.referred_user_id),
    }


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
            .where(
                (ReferralConversion.status == ReferralConversionStatus.REVIEW_REQUIRED)
                | (ReferralConversion.fraud_status != ReferralFraudStatus.CLEAR)
            )
            .order_by(ReferralConversion.created_at.desc())
            .limit(100)
        ).all()
    )
    return [_admin_conversion_row(db, row) for row in rows]


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
