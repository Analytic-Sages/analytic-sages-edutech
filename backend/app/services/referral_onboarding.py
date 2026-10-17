"""Application, cohort, onboarding and referral-link workflows.

These services extend the existing referral ledger and attribution engine. They do
not create or settle commissions; the established payment-level commission service
remains the source of truth.
"""
from __future__ import annotations

from datetime import UTC, datetime
import re
from urllib.parse import urlparse
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.referrals import ReferralPartnerStatus
from app.models.classroom import Cohort
from app.models.course import Course
from app.models.referral import (
    ReferralAttribution,
    ReferralAuditEvent,
    ReferralClick,
    ReferralConversion,
    ReferralLink,
    ReferralPartner,
    ReferralPartnerApplication,
    ReferralPartnerCohort,
    ReferralProgramResources,
)
from app.models.user import User
from app.services.referrals import generate_referral_code

APPLICATION_STATUSES = {
    "submitted", "under_review", "shortlisted", "interviewed", "approved",
    "onboarding", "active", "rejected", "waitlisted", "suspended", "inactive",
}
ALLOWED_TRANSITIONS = {
    "submitted": {"under_review", "rejected", "waitlisted"},
    "under_review": {"shortlisted", "interviewed", "rejected", "waitlisted"},
    "shortlisted": {"interviewed", "rejected", "waitlisted", "under_review"},
    "interviewed": {"approved", "rejected", "waitlisted", "under_review"},
    "approved": {"onboarding", "rejected", "waitlisted"},
    "onboarding": {"active", "suspended", "inactive"},
    "active": {"suspended", "inactive"},
    "suspended": {"active", "inactive"},
    "waitlisted": {"under_review", "shortlisted", "rejected"},
    "rejected": set(),
    "inactive": {"active", "suspended"},
}
SCORE_WEIGHTS = {
    "audience_relevance": 30,
    "promotion_strategy": 25,
    "credibility_engagement": 20,
    "relevant_experience": 15,
    "communication_professionalism": 10,
}
COHORT_MEMBER_STATUSES = ("approved", "onboarding", "active", "suspended", "inactive")


def normalize_email(email: str) -> str:
    return email.strip().casefold()


class ReferralOnboardingService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def submit_application(
        self, *, payload, user: User | None, actor_id: UUID | None = None
    ) -> ReferralPartnerApplication:
        if not payload.terms_accepted:
            raise HTTPException(status_code=400, detail="You must accept the Referral Partner terms.")
        resources = self.db.get(ReferralProgramResources, 1)
        current_terms_version = resources.terms_version if resources else "referral-partner-v1"
        if payload.terms_version != current_terms_version:
            raise HTTPException(status_code=409, detail="The programme terms have changed. Refresh the page and accept the current version.")
        email = normalize_email(payload.email)
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise HTTPException(status_code=400, detail="Enter a valid email address.")
        for candidate in [payload.linkedin_url, *(item.get("url", "") for item in payload.social_profiles)]:
            if candidate:
                parsed = urlparse(candidate.strip())
                if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                    raise HTTPException(status_code=400, detail="Social profile links must use a valid http or https URL.")
        if user and normalize_email(user.email) != email:
            raise HTTPException(status_code=400, detail="Use the email address on your signed-in account.")
        if user and not user.email_verified:
            raise HTTPException(status_code=400, detail="Verify your account email before applying.")
        existing = self.db.scalar(
            select(ReferralPartnerApplication).where(
                ReferralPartnerApplication.email_normalized == email
            )
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"An application already exists for this email (status: {existing.status}).",
            )
        if user:
            existing_partner = self.db.scalar(
                select(ReferralPartner).where(ReferralPartner.user_id == user.id)
            )
            if existing_partner and existing_partner.status != ReferralPartnerStatus.PENDING:
                raise HTTPException(status_code=409, detail="This account already has a non-pending Referral Partner profile.")
        valid_slugs = set()
        if payload.interested_courses:
            valid_slugs = set(self.db.scalars(
                select(Course.slug).where(
                    Course.slug.in_(payload.interested_courses),
                    Course.published.is_(True),
                    Course.referral_commission_eligible.is_(True),
                    Course.is_free.is_(False),
                )
            ).all())
            invalid = set(payload.interested_courses) - valid_slugs
            if invalid:
                raise HTTPException(status_code=400, detail="One or more selected courses are unavailable.")
        now = datetime.now(UTC)
        application = ReferralPartnerApplication(
            user_id=user.id if user else None,
            full_name=payload.full_name.strip(),
            email=payload.email.strip(),
            email_normalized=email,
            country=(payload.country or "").strip() or None,
            timezone=(payload.timezone or "").strip() or None,
            linkedin_url=(payload.linkedin_url or "").strip() or None,
            social_profiles=payload.social_profiles,
            communities=(payload.communities or "").strip() or None,
            audience_size=(payload.audience_size or "").strip() or None,
            audience_engagement=(payload.audience_engagement or "").strip() or None,
            relevant_experience=(payload.relevant_experience or "").strip() or None,
            partnership_experience=(payload.partnership_experience or "").strip() or None,
            interested_courses=sorted(valid_slugs),
            promotion_channels=[x.strip() for x in payload.promotion_channels if x.strip()],
            marketing_plan=payload.marketing_plan.strip(),
            terms_accepted_at=now,
            terms_version=current_terms_version,
            marketing_guidelines_accepted_at=now,
            status="submitted",
        )
        self.db.add(application)
        self.db.flush()
        self._audit(
            actor_id=actor_id or (user.id if user else None),
            action="application.submitted",
            entity_type="referral_partner_application",
            entity_id=application.id,
            after={"status": application.status, "email_normalized": email},
        )
        self.db.commit()
        self.db.refresh(application)
        return application

    def list_applications(self, *, status_filter: str | None = None, limit: int = 200):
        stmt = select(ReferralPartnerApplication).order_by(ReferralPartnerApplication.created_at.desc())
        if status_filter:
            if status_filter not in APPLICATION_STATUSES:
                raise HTTPException(status_code=400, detail="Invalid application status.")
            stmt = stmt.where(ReferralPartnerApplication.status == status_filter)
        return list(self.db.scalars(stmt.limit(min(max(limit, 1), 500))).all())

    def patch_application(
        self, *, application_id: UUID, payload, actor: User
    ) -> ReferralPartnerApplication:
        application = self.db.scalar(
            select(ReferralPartnerApplication)
            .where(ReferralPartnerApplication.id == application_id)
            .with_for_update()
        )
        if not application:
            raise HTTPException(status_code=404, detail="Application not found.")
        before = {
            "status": application.status,
            "cohort_id": str(application.cohort_id) if application.cohort_id else None,
            "score_total": application.score_total,
            "scores": application.scores,
            "approved_by": str(application.approved_by) if application.approved_by else None,
            "approved_at": application.approved_at.isoformat() if application.approved_at else None,
        }
        updates = payload.model_dump(exclude_unset=True)
        next_status = updates.get("status")
        if next_status is not None:
            if next_status not in APPLICATION_STATUSES:
                raise HTTPException(status_code=400, detail="Invalid application status.")
            if next_status != application.status and next_status not in ALLOWED_TRANSITIONS.get(application.status, set()):
                raise HTTPException(
                    status_code=409,
                    detail=f"Invalid application transition: {application.status} → {next_status}.",
                )
        scores = updates.get("scores")
        if scores is not None:
            unknown = set(scores) - set(SCORE_WEIGHTS)
            if unknown:
                raise HTTPException(status_code=400, detail=f"Unknown score criteria: {', '.join(sorted(unknown))}.")
            for key, value in scores.items():
                if not isinstance(value, int) or value < 0 or value > SCORE_WEIGHTS[key]:
                    raise HTTPException(status_code=400, detail=f"{key} must be between 0 and {SCORE_WEIGHTS[key]}.")
            application.scores = scores
            application.score_total = sum(scores.values())
            application.reviewer_id = actor.id
        cohort_id = updates.get("cohort_id")
        if cohort_id is not None:
            cohort = self._lock_cohort(cohort_id)
            if not cohort or not cohort.is_active:
                raise HTTPException(status_code=400, detail="Choose an active referral-partner cohort.")
            self._assert_capacity(cohort, application)
            application.cohort_id = cohort.id
            if application.partner_id:
                assigned_partner = self.db.get(ReferralPartner, application.partner_id)
                if assigned_partner:
                    assigned_partner.cohort_id = cohort.id
        if next_status == "approved" and application.status != "approved":
            if application.status != "interviewed":
                raise HTTPException(status_code=409, detail="Interview and record a decision before approval.")
            if application.interview_status != "completed" or application.interview_decision != "recommend":
                raise HTTPException(status_code=409, detail="Record a completed interview and a 'recommend' decision before approval.")
            if not application.interview_notes or not application.interview_reason:
                raise HTTPException(status_code=409, detail="Record interview notes and the decision reason before approval.")
            if not set(SCORE_WEIGHTS).issubset(set(application.scores or {})):
                raise HTTPException(status_code=409, detail="Score all five application criteria before approval.")
            cohort = self._lock_cohort(application.cohort_id) if application.cohort_id else self._default_cohort_for_update()
            if not cohort or not cohort.is_active:
                raise HTTPException(status_code=409, detail="No active cohort is available.")
            self._assert_capacity(cohort, application)
            application.cohort_id = cohort.id
            application.approved_at = datetime.now(UTC)
            application.approved_by = actor.id
            application.reviewer_id = actor.id
            self._attach_partner_if_account_exists(application)
            if application.partner_id:
                approved_partner = self.db.get(ReferralPartner, application.partner_id)
                if approved_partner:
                    approved_partner.cohort_id = cohort.id
                    approved_partner.approved_at = application.approved_at
                    approved_partner.approved_by = actor.id
        if next_status == "onboarding":
            self._attach_partner_if_account_exists(application)
            if not application.partner_id:
                raise HTTPException(status_code=409, detail="The applicant must claim the approved application using a verified account first.")
        if next_status == "active" and application.status != "active":
            if application.status not in {"suspended", "inactive"} or not application.partner_id:
                raise HTTPException(status_code=409, detail="Partners can only become active through onboarding completion.")
            partner = self.db.get(ReferralPartner, application.partner_id)
            if not partner or partner.onboarding_completed_at is None:
                raise HTTPException(status_code=409, detail="Complete onboarding before reactivation.")
            partner.status = ReferralPartnerStatus.ACTIVE
            self._set_link_statuses(partner.id, "active", actor.id)
        review_fields = {"scores", "review_notes", "rejection_reason", "cohort_id"}
        interview_fields = {"interview_at", "interview_status", "interview_notes", "interview_decision", "interview_reason", "follow_up_actions"}
        if review_fields.intersection(updates):
            application.reviewer_id = actor.id
        if interview_fields.intersection(updates):
            application.interview_reviewer_id = actor.id
        if next_status == "rejected" and not (updates.get("rejection_reason") or application.rejection_reason):
            raise HTTPException(status_code=400, detail="Record a rejection reason.")
        for key, value in updates.items():
            if key in {"status", "cohort_id", "scores"}:
                continue
            setattr(application, key, value)
        if next_status is not None:
            if next_status != application.status:
                application.reviewer_id = actor.id
            application.status = next_status
        if application.status in {"suspended", "inactive"} and application.partner_id:
            partner = self.db.get(ReferralPartner, application.partner_id)
            if partner:
                partner.status = ReferralPartnerStatus.SUSPENDED
                self._set_link_statuses(partner.id, "inactive", actor.id)
        self._audit(
            actor_id=actor.id,
            action="application.updated",
            entity_type="referral_partner_application",
            entity_id=application.id,
            note=updates.get("review_notes") or updates.get("rejection_reason"),
            before=before,
            after={
                "status": application.status,
                "cohort_id": str(application.cohort_id) if application.cohort_id else None,
                "score_total": application.score_total,
                "scores": application.scores,
                "approved_by": str(application.approved_by) if application.approved_by else None,
                "approved_at": application.approved_at.isoformat() if application.approved_at else None,
            },
        )
        self.db.commit()
        self.db.refresh(application)
        return application

    def claim_approved_application(self, *, user: User) -> ReferralPartnerApplication:
        if not user.email_verified:
            raise HTTPException(status_code=403, detail="Verify your email before claiming an application.")
        email = normalize_email(user.email)
        application = self.db.scalar(
            select(ReferralPartnerApplication)
            .where(ReferralPartnerApplication.email_normalized == email)
            .with_for_update()
        )
        if not application or application.status not in {"approved", "onboarding"}:
            raise HTTPException(status_code=404, detail="No approved application was found for this account.")
        if application.user_id and application.user_id != user.id:
            raise HTTPException(status_code=409, detail="This application is linked to another account.")
        self._attach_partner(application, user)
        application.status = "onboarding"
        self._audit(
            actor_id=user.id,
            action="application.claimed",
            entity_type="referral_partner_application",
            entity_id=application.id,
            after={"user_id": str(user.id), "partner_id": str(application.partner_id)},
        )
        self.db.commit()
        self.db.refresh(application)
        return application

    def complete_onboarding(self, *, partner: ReferralPartner, payload, actor: User) -> ReferralPartner:
        if partner.user_id != actor.id:
            raise HTTPException(status_code=403, detail="You can only complete onboarding for your own partner account.")
        application = self.db.scalar(
            select(ReferralPartnerApplication)
            .where(ReferralPartnerApplication.partner_id == partner.id)
            .with_for_update()
        )
        if not application or application.status not in {"approved", "onboarding"}:
            raise HTTPException(status_code=409, detail="An approved application is required to complete onboarding.")
        if partner.status != ReferralPartnerStatus.PENDING:
            raise HTTPException(status_code=409, detail="Only a pending partner can complete onboarding. Ask an administrator to review your current status.")
        if not payload.profile_completed or not payload.terms_accepted or not payload.marketing_guidelines_accepted:
            raise HTTPException(status_code=400, detail="Complete your profile and acknowledge both program terms and marketing guidelines.")
        resources = self.db.get(ReferralProgramResources, 1)
        current_terms_version = resources.terms_version if resources else "referral-partner-v1"
        if payload.terms_version != current_terms_version:
            raise HTTPException(status_code=409, detail="The programme terms have changed. Review and accept the current version.")
        if not application.cohort_id:
            raise HTTPException(status_code=409, detail="Your application must be assigned to a cohort.")
        link_count = self.db.scalar(
            select(func.count(ReferralLink.id)).where(
                ReferralLink.partner_id == partner.id,
                ReferralLink.status != "revoked",
            )
        ) or 0
        if link_count < 1:
            raise HTTPException(status_code=409, detail="Create or request at least one referral link before activation.")
        now = datetime.now(UTC)
        before = {"status": partner.status.value, "onboarding_completed_at": None}
        partner.profile_completed_at = now
        partner.marketing_guidelines_accepted_at = now
        partner.onboarding_terms_version = payload.terms_version
        partner.onboarding_completed_at = now
        partner.cohort_id = application.cohort_id
        partner.status = ReferralPartnerStatus.ACTIVE
        partner.approved_at = partner.approved_at or application.approved_at
        partner.approved_by = partner.approved_by or application.approved_by
        if not partner.referral_code:
            partner.referral_code = self._unique_code()
        application.marketing_guidelines_accepted_at = now
        application.status = "active"
        self._set_link_statuses(partner.id, "active", actor.id)
        self._audit(
            actor_id=actor.id,
            action="partner.onboarding_completed",
            entity_type="referral_partner",
            entity_id=partner.id,
            before=before,
            after={"status": partner.status.value, "onboarding_terms_version": payload.terms_version},
        )
        self.db.commit()
        self.db.refresh(partner)
        return partner

    def create_link(self, *, partner: ReferralPartner, payload, actor: User) -> ReferralLink:
        if partner.status not in {ReferralPartnerStatus.PENDING, ReferralPartnerStatus.ACTIVE}:
            raise HTTPException(status_code=403, detail="This partner cannot create referral links.")
        application = self.db.scalar(
            select(ReferralPartnerApplication).where(
                ReferralPartnerApplication.partner_id == partner.id
            )
        )
        if partner.status != ReferralPartnerStatus.ACTIVE and (
            not application or application.status not in {"approved", "onboarding"}
        ):
            raise HTTPException(status_code=403, detail="An approved application is required before link setup.")
        if payload.course_id and payload.cohort_id:
            raise HTTPException(status_code=400, detail="A link can target a course or a programme, not both.")
        destination = self.settings.referral_default_redirect_path
        target_type = "general"
        target_slug = None
        if payload.course_id:
            course = self.db.get(Course, payload.course_id)
            if not course or not course.published or not course.referral_commission_eligible or course.is_free:
                raise HTTPException(status_code=400, detail="That course is not currently eligible for referrals.")
            destination = f"/courses/{course.slug}"
            target_type = "course"
            target_slug = course.slug
        elif payload.cohort_id:
            cohort = self.db.get(Cohort, payload.cohort_id)
            if not cohort or not cohort.referral_commission_eligible or cohort.price <= 0 or cohort.status.value not in {"open", "active"}:
                raise HTTPException(status_code=400, detail="That programme is not currently eligible for referrals.")
            destination = f"/programs/{cohort.slug}"
            target_type = "programme"
            target_slug = cohort.slug
        code = self._unique_code()
        link = ReferralLink(
            partner_id=partner.id,
            course_id=payload.course_id,
            cohort_id=payload.cohort_id,
            target_type=target_type,
            target_slug=target_slug,
            campaign_label=(payload.campaign_label or "").strip() or None,
            campaign_channel=(payload.campaign_channel or "").strip() or None,
            code=code,
            destination_path=destination,
            status="active" if partner.status == ReferralPartnerStatus.ACTIVE else "inactive",
        )
        self.db.add(link)
        self.db.flush()
        if application and application.status == "approved":
            application.status = "onboarding"
        self._audit(
            actor_id=actor.id,
            action="referral_link.created",
            entity_type="referral_link",
            entity_id=link.id,
            after={"partner_id": str(partner.id), "code": code, "destination_path": destination, "status": link.status},
        )
        self.db.commit()
        self.db.refresh(link)
        return link

    def list_links(
        self,
        *,
        partner: ReferralPartner,
        admin: bool = False,
        partner_id: UUID | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        course_id: UUID | None = None,
        campaign: str | None = None,
        status_filter: str | None = None,
        link_id: UUID | None = None,
    ):
        target_partner_id = partner_id if admin and partner_id else partner.id
        stmt = select(ReferralLink).where(ReferralLink.partner_id == target_partner_id)
        if course_id:
            stmt = stmt.where(ReferralLink.course_id == course_id)
        if campaign:
            pattern = f"%{campaign.strip()}%"
            stmt = stmt.where(or_(ReferralLink.campaign_label.ilike(pattern), ReferralLink.campaign_channel.ilike(pattern)))
        if status_filter:
            if status_filter not in {"inactive", "active", "revoked"}:
                raise HTTPException(status_code=400, detail="Invalid referral link status.")
            stmt = stmt.where(ReferralLink.status == status_filter)
        if link_id:
            stmt = stmt.where(ReferralLink.id == link_id)
        links = list(self.db.scalars(stmt.order_by(ReferralLink.created_at.desc())).all())
        result = []
        for link in links:
            course = self.db.get(Course, link.course_id) if link.course_id else None
            cohort = self.db.get(Cohort, link.cohort_id) if link.cohort_id else None
            target_available = True
            unavailable_reason = None
            if link.target_type == "course":
                if not course:
                    target_available, unavailable_reason = False, "The original course is no longer available."
                elif not course.published or not course.referral_commission_eligible or course.is_free:
                    target_available, unavailable_reason = False, "The original course is unpublished or no longer eligible."
            elif link.target_type == "programme":
                if not cohort:
                    target_available, unavailable_reason = False, "The original programme is no longer available."
                elif not cohort.referral_commission_eligible or cohort.price <= 0 or cohort.status not in {"open", "active"}:
                    target_available, unavailable_reason = False, "The original programme is closed or no longer eligible."
            click_stmt = select(func.count(ReferralClick.id)).where(ReferralClick.referral_link_id == link.id)
            conversion_stmt = select(ReferralConversion).where(ReferralConversion.referral_link_id == link.id)
            if start_at:
                click_stmt = click_stmt.where(ReferralClick.created_at >= start_at)
                conversion_stmt = conversion_stmt.where(ReferralConversion.created_at >= start_at)
            if end_at:
                click_stmt = click_stmt.where(ReferralClick.created_at < end_at)
                conversion_stmt = conversion_stmt.where(ReferralConversion.created_at < end_at)
            clicks = int(self.db.scalar(click_stmt) or 0)
            conv_rows = list(self.db.scalars(conversion_stmt).all())
            paid_products = {
                row.enrollment_id if row.enrollment_id else (row.referred_user_id, row.course_id, row.cohort_id)
                for row in conv_rows
            }
            commission_by_currency: dict[str, Decimal] = {}
            for row in conv_rows:
                commission_by_currency[row.currency] = commission_by_currency.get(row.currency, Decimal("0.00")) + row.commission_amount
            currencies = set(commission_by_currency)
            single_currency = next(iter(currencies)) if len(currencies) == 1 else None
            result.append({
                "id": link.id, "partner_id": link.partner_id,
                "course_id": link.course_id, "course_title": course.title if course else (link.target_slug if link.target_type == "course" else None),
                "course_slug": course.slug if course else None,
                "cohort_id": link.cohort_id, "cohort_name": cohort.name if cohort else (link.target_slug if link.target_type == "programme" else None),
                "campaign_label": link.campaign_label, "campaign_channel": link.campaign_channel,
                "code": link.code, "destination_path": link.destination_path,
                "url": f"{self.settings.frontend_url.rstrip('/')}/ref/{link.code}",
                "target_type": link.target_type, "target_slug": link.target_slug,
                "target_available": target_available, "unavailable_reason": unavailable_reason,
                "status": link.status, "clicks": clicks,
                "paid_enrollments": len(paid_products),
                "conversion_rate": (Decimal(len(paid_products)) * Decimal("100") / Decimal(clicks)).quantize(Decimal("0.01")) if clicks else Decimal("0.00"),
                "commission_amount": commission_by_currency[single_currency] if single_currency else None,
                "commission_currency": single_currency,
                "commission_by_currency": commission_by_currency,
                "created_at": link.created_at, "revoked_at": link.revoked_at,
            })
        return result

    def patch_link(self, *, link_id: UUID, actor: User, partner: ReferralPartner | None = None, status_value: str, reason: str | None = None):
        link = self.db.scalar(select(ReferralLink).where(ReferralLink.id == link_id).with_for_update())
        if not link or (partner and link.partner_id != partner.id):
            raise HTTPException(status_code=404, detail="Referral link not found.")
        if status_value not in {"inactive", "revoked", "active"}:
            raise HTTPException(status_code=400, detail="Invalid referral link status.")
        if link.status == "revoked" and status_value != "revoked":
            raise HTTPException(status_code=409, detail="Revoked links cannot be reactivated; create a new link.")
        owner = self.db.get(ReferralPartner, link.partner_id)
        if status_value == "active" and (not owner or owner.status != ReferralPartnerStatus.ACTIVE):
            raise HTTPException(status_code=409, detail="Only active partners can activate links.")
        before = {"status": link.status}
        link.status = status_value
        if status_value == "revoked":
            link.revoked_at = datetime.now(UTC)
            link.revoked_by = actor.id
            link.revocation_reason = reason
        self._audit(
            actor_id=actor.id,
            action=f"referral_link.{status_value}",
            entity_type="referral_link",
            entity_id=link.id,
            note=reason,
            before=before,
            after={"status": link.status},
        )
        self.db.commit()
        self.db.refresh(link)
        return link

    def list_cohorts(self):
        cohorts = list(self.db.scalars(select(ReferralPartnerCohort).order_by(ReferralPartnerCohort.created_at.asc())).all())
        return [self._cohort_payload(c) for c in cohorts]

    def create_cohort(self, *, name: str, capacity: int, is_active: bool, actor: User):
        cohort = ReferralPartnerCohort(name=name.strip(), capacity=capacity, is_active=is_active, created_by=actor.id)
        self.db.add(cohort)
        self.db.flush()
        self._audit(actor_id=actor.id, action="cohort.created", entity_type="referral_partner_cohort", entity_id=cohort.id, after={"name": cohort.name, "capacity": capacity})
        self.db.commit()
        self.db.refresh(cohort)
        return self._cohort_payload(cohort)

    def patch_cohort(self, *, cohort_id: UUID, capacity: int | None, is_active: bool | None, actor: User):
        cohort = self._lock_cohort(cohort_id)
        if not cohort:
            raise HTTPException(status_code=404, detail="Cohort not found.")
        before = {"capacity": cohort.capacity, "is_active": cohort.is_active}
        if capacity is not None:
            count = self._approved_count(cohort.id)
            if capacity < count:
                raise HTTPException(status_code=409, detail=f"Capacity cannot be below the {count} already approved cohort members.")
            cohort.capacity = capacity
        if is_active is not None:
            cohort.is_active = is_active
        self._audit(actor_id=actor.id, action="cohort.updated", entity_type="referral_partner_cohort", entity_id=cohort.id, before=before, after={"capacity": cohort.capacity, "is_active": cohort.is_active})
        self.db.commit()
        self.db.refresh(cohort)
        return self._cohort_payload(cohort)

    def _attach_partner_if_account_exists(self, application: ReferralPartnerApplication) -> None:
        if application.partner_id or not application.user_id:
            # Public submissions are not attached to an account based only on an
            # email address. The verified owner must explicitly claim the approval.
            return
        user = self.db.get(User, application.user_id)
        if user and user.email_verified:
            self._attach_partner(application, user)

    def _attach_partner(self, application: ReferralPartnerApplication, user: User) -> ReferralPartner:
        if normalize_email(user.email) != application.email_normalized:
            raise HTTPException(status_code=403, detail="Application email does not match the verified account.")
        partner = self.db.scalar(select(ReferralPartner).where(ReferralPartner.user_id == user.id).with_for_update())
        if not partner:
            partner = ReferralPartner(
                user_id=user.id,
                status=ReferralPartnerStatus.PENDING,
                display_name=application.full_name,
                social_handle=application.linkedin_url,
                promotion_channels=", ".join(application.promotion_channels),
                terms_accepted_at=application.terms_accepted_at,
                cohort_id=application.cohort_id,
            )
            self.db.add(partner)
            self.db.flush()
        elif partner.status != ReferralPartnerStatus.PENDING:
            raise HTTPException(status_code=409, detail="This account already has a non-pending Referral Partner profile. Contact an administrator.")
        application.user_id = user.id
        application.partner_id = partner.id
        partner.cohort_id = application.cohort_id
        partner.approved_at = partner.approved_at or application.approved_at
        partner.approved_by = partner.approved_by or application.approved_by
        return partner

    def _default_cohort_for_update(self) -> ReferralPartnerCohort | None:
        return self.db.scalar(
            select(ReferralPartnerCohort).where(ReferralPartnerCohort.name == "Cohort 1").with_for_update()
        )

    def _lock_cohort(self, cohort_id: UUID | None) -> ReferralPartnerCohort | None:
        if not cohort_id:
            return None
        return self.db.scalar(select(ReferralPartnerCohort).where(ReferralPartnerCohort.id == cohort_id).with_for_update())

    def _approved_count(self, cohort_id: UUID) -> int:
        return int(self.db.scalar(
            select(func.count(ReferralPartnerApplication.id)).where(
                ReferralPartnerApplication.cohort_id == cohort_id,
                ReferralPartnerApplication.status.in_(COHORT_MEMBER_STATUSES),
            )
        ) or 0)

    def _assert_capacity(self, cohort: ReferralPartnerCohort, application: ReferralPartnerApplication) -> None:
        count = self._approved_count(cohort.id)
        if application.cohort_id == cohort.id and application.status in COHORT_MEMBER_STATUSES:
            count -= 1
        if count >= cohort.capacity:
            raise HTTPException(status_code=409, detail=f"{cohort.name} is full ({cohort.capacity} approved partners). Waitlist the applicant or choose another cohort.")

    def _cohort_payload(self, cohort: ReferralPartnerCohort) -> dict:
        count = self._approved_count(cohort.id)
        return {"id": cohort.id, "name": cohort.name, "capacity": cohort.capacity, "approved_count": count, "remaining_slots": max(0, cohort.capacity - count), "is_active": cohort.is_active, "created_at": cohort.created_at}

    def _set_link_statuses(self, partner_id: UUID, status_value: str, actor_id: UUID | None = None) -> None:
        for link in self.db.scalars(
            select(ReferralLink).where(ReferralLink.partner_id == partner_id, ReferralLink.status != "revoked")
        ).all():
            if link.status == status_value:
                continue
            previous = link.status
            link.status = status_value
            self._audit(
                actor_id=actor_id,
                action=f"referral_link.{status_value}",
                entity_type="referral_link",
                entity_id=link.id,
                before={"status": previous},
                after={"status": status_value},
            )

    def _unique_code(self) -> str:
        for _ in range(30):
            # Prefix link codes so they occupy a distinct namespace from legacy 8-char partner codes.
            code = "RL" + generate_referral_code()
            exists_partner = self.db.scalar(select(ReferralPartner.id).where(ReferralPartner.referral_code == code))
            exists_link = self.db.scalar(select(ReferralLink.id).where(ReferralLink.code == code))
            if not exists_partner and not exists_link:
                return code
        raise HTTPException(status_code=500, detail="Could not generate a unique referral link code.")

    def _audit(self, *, actor_id: UUID | None, action: str, entity_type: str, entity_id: UUID | None, note: str | None = None, before: dict | None = None, after: dict | None = None) -> None:
        self.db.add(ReferralAuditEvent(
            actor_id=actor_id, action=action, entity_type=entity_type, entity_id=entity_id,
            note=note, before_json=before, after_json=after,
        ))
