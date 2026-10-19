"""Regression tests for referral applications, cohort targets and link attribution."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.core.config import get_settings
from app.core.referrals import ReferralPartnerStatus
from app.core.roles import UserRole
from app.db.session import SessionLocal
from app.models.course import Course
from app.models.referral import (
    ReferralAttribution,
    ReferralAuditEvent,
    ReferralClick,
    ReferralLink,
    ReferralPartner,
    ReferralPartnerApplication,
    ReferralPartnerCohort,
)
from app.models.user import User
from app.schemas.referral_onboarding import ReferralPartnerApplicationCreate, ReferralPartnerApplicationPatch
from app.services.referral_onboarding import ReferralOnboardingService
from app.services.referrals import ReferralAttributionService, ReferralDashboardService

SCORES = {
    "audience_relevance": 28,
    "promotion_strategy": 22,
    "credibility_engagement": 18,
    "relevant_experience": 14,
    "communication_professionalism": 9,
}


def _make_user(db, email: str, role: UserRole = UserRole.STUDENT) -> User:
    user = User(
        email=email,
        full_name="Referral Test User",
        role=role,
        email_verified=True,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _application_payload(email: str) -> ReferralPartnerApplicationCreate:
    return ReferralPartnerApplicationCreate(
        full_name="Referral Applicant",
        email=email,
        whatsapp_number="+2348012345678",
        telegram_id="@referral_applicant",
        country="Nigeria",
        timezone="Africa/Lagos",
        linkedin_url="https://www.linkedin.com/in/referral-applicant",
        social_profiles=[{"platform": "X", "url": "https://x.com/referral-applicant"}],
        communities="A focused developer community",
        audience_size="300 members",
        audience_engagement="Weekly discussions and event attendance",
        relevant_experience="Organised technical learning sessions and workshops.",
        partnership_experience="Worked with community partners.",
        interested_courses=[],
        promotion_channels=["LinkedIn", "Community"],
        marketing_plan="I will share course-specific posts, explain the curriculum accurately, and answer learner questions.",
        terms_accepted=True,
    )


def _prepare_interview(service: ReferralOnboardingService, application, admin: User) -> None:
    service.patch_application(
        application_id=application.id,
        payload=ReferralPartnerApplicationPatch(status="under_review"),
        actor=admin,
    )
    service.patch_application(
        application_id=application.id,
        payload=ReferralPartnerApplicationPatch(status="shortlisted", scores=SCORES),
        actor=admin,
    )
    service.patch_application(
        application_id=application.id,
        payload=ReferralPartnerApplicationPatch(
            status="interviewed",
            interview_status="completed",
            interview_decision="recommend",
            interview_notes="Clear, practical plan and relevant audience.",
            interview_reason="Recommend based on fit and credible promotion approach.",
            scores=SCORES,
        ),
        actor=admin,
    )


def test_referral_application_rejects_duplicates_and_records_terms():
    db = SessionLocal()
    email = f"ref-app-{uuid.uuid4().hex[:10]}@example.test"
    app_id = None
    try:
        service = ReferralOnboardingService(db, get_settings())
        pending_before = ReferralDashboardService(db, get_settings()).admin_overview()["pending_applications"]
        application = service.submit_application(payload=_application_payload(email), user=None)
        app_id = application.id
        assert application.status == "submitted"
        assert application.terms_accepted_at is not None
        assert application.terms_version == "referral-partner-v1"
        assert application.whatsapp_number == "+2348012345678"
        assert application.telegram_id == "@referral_applicant"
        pending_after = ReferralDashboardService(db, get_settings()).admin_overview()["pending_applications"]
        assert pending_after == pending_before + 1
        with pytest.raises(HTTPException) as exc:
            service.submit_application(payload=_application_payload(email), user=None)
        assert exc.value.status_code == 409
    finally:
        if app_id:
            db.query(ReferralAuditEvent).filter(ReferralAuditEvent.entity_id == app_id).delete(synchronize_session=False)
            db.query(ReferralPartnerApplication).filter(ReferralPartnerApplication.id == app_id).delete(synchronize_session=False)
            db.commit()
        db.close()


def test_cohort_target_is_informational_when_approving_more_than_target():
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:10]
    admin_email = f"ref-admin-{suffix}@example.test"
    app_ids = []
    cohort_id = None
    admin_id = None
    try:
        admin = _make_user(db, admin_email, UserRole.ADMIN)
        admin_id = admin.id
        db.commit()
        service = ReferralOnboardingService(db, get_settings())
        cohort = service.create_cohort(name=f"Test cohort {suffix}", capacity=1, is_active=True, actor=admin)
        cohort_id = cohort["id"]
        first = service.submit_application(payload=_application_payload(f"ref-first-{suffix}@example.test"), user=None)
        app_ids.append(first.id)
        _prepare_interview(service, first, admin)
        approved_first = service.patch_application(
            application_id=first.id,
            payload=ReferralPartnerApplicationPatch(status="approved", cohort_id=cohort_id),
            actor=admin,
        )
        assert approved_first.status == "approved"
        assert approved_first.cohort_id == cohort_id

        second = service.submit_application(payload=_application_payload(f"ref-second-{suffix}@example.test"), user=None)
        app_ids.append(second.id)
        _prepare_interview(service, second, admin)
        approved_second = service.patch_application(
            application_id=second.id,
            payload=ReferralPartnerApplicationPatch(status="approved", cohort_id=cohort_id),
            actor=admin,
        )
        assert approved_second.status == "approved"
        assert approved_second.cohort_id == cohort_id
        cohort_row = next(row for row in service.list_cohorts() if row["id"] == cohort_id)
        assert cohort_row["approved_count"] == 2
        assert cohort_row["remaining_slots"] == 0
    finally:
        if app_ids:
            db.query(ReferralAuditEvent).filter(ReferralAuditEvent.entity_id.in_(app_ids)).delete(synchronize_session=False)
            db.query(ReferralPartnerApplication).filter(ReferralPartnerApplication.id.in_(app_ids)).delete(synchronize_session=False)
        if cohort_id:
            db.query(ReferralAuditEvent).filter(ReferralAuditEvent.entity_id == cohort_id).delete(synchronize_session=False)
            db.query(ReferralPartnerCohort).filter(ReferralPartnerCohort.id == cohort_id).delete(synchronize_session=False)
        if admin_id:
            db.query(ReferralAuditEvent).filter(ReferralAuditEvent.actor_id == admin_id).delete(synchronize_session=False)
            db.query(User).filter(User.id == admin_id).delete(synchronize_session=False)
        db.commit()
        db.close()


def test_course_campaign_link_tracks_link_identity_and_uses_server_destination():
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:10]
    email = f"ref-link-{suffix}@example.test"
    user_id = None
    partner_id = None
    course_id = None
    link_ids = []
    try:
        user = _make_user(db, email)
        user_id = user.id
        course = Course(
            slug=f"ref-course-{suffix}",
            title="Referral test course",
            description="Test course",
            long_description="Test course",
            category="Data",
            difficulty="Beginner",
            duration="1 week",
            estimated_minutes=60,
            lessons_count=1,
            price=100,
            currency="USD",
            delivery_type="self_paced",
            is_free=False,
            referral_commission_eligible=True,
            published=True,
        )
        db.add(course)
        db.flush()
        course_id = course.id
        partner = ReferralPartner(
            user_id=user.id,
            status=ReferralPartnerStatus.ACTIVE,
            referral_code=f"LEGACY{suffix.upper()}",
            display_name="Referral Link Partner",
            terms_accepted_at=datetime.now(UTC),
            onboarding_completed_at=datetime.now(UTC),
        )
        db.add(partner)
        db.commit()
        db.refresh(partner)
        partner_id = partner.id

        service = ReferralOnboardingService(db, get_settings())
        link = service.create_link(
            partner=partner,
            payload=SimpleNamespace(
                course_id=course.id,
                cohort_id=None,
                campaign_label="LinkedIn launch",
                campaign_channel="LinkedIn",
            ),
            actor=user,
        )
        link_ids.append(link.id)
        assert link.status == "active"
        assert link.destination_path == f"/courses/{course.slug}"
        second_link = service.create_link(
            partner=partner,
            payload=SimpleNamespace(
                course_id=course.id,
                cohort_id=None,
                campaign_label="Telegram community",
                campaign_channel="Telegram",
            ),
            actor=user,
        )
        link_ids.append(second_link.id)
        assert second_link.id != link.id
        assert second_link.code != link.code
        assert second_link.campaign_label == "Telegram community"

        tracker = ReferralAttributionService(db, get_settings())
        for index, created_link in enumerate((link, second_link), start=1):
            ok, redirect = tracker.track_click(
                code=created_link.code,
                anonymous_visitor_id=f"visitor-{suffix}-{index}",
                landing_path=f"/ref/{created_link.code}",
                ip="192.0.2.10",
                user_agent="Referral test",
                destination="/programs",
            )
            assert ok is True
            assert redirect == f"/courses/{course.slug}"
            click = db.scalar(select(ReferralClick).where(ReferralClick.referral_link_id == created_link.id))
            attribution = db.scalar(select(ReferralAttribution).where(ReferralAttribution.referral_link_id == created_link.id))
            assert click is not None
            assert attribution is not None
            assert click.partner_id == partner.id
            assert attribution.partner_id == partner.id

        course.published = False
        db.commit()
        ok, redirect = tracker.track_click(
            code=link.code,
            anonymous_visitor_id=f"visitor-{suffix}-unpublished",
            landing_path=f"/ref/{link.code}",
            ip="192.0.2.10",
            user_agent="Referral test",
            destination="/programs",
        )
        assert ok is False
        assert redirect == get_settings().referral_default_redirect_path
        link_rows = service.list_links(partner=partner)
        first_link = next(row for row in link_rows if row["id"] == link.id)
        assert first_link["target_available"] is False
    finally:
        if link_ids:
            db.query(ReferralClick).filter(ReferralClick.referral_link_id.in_(link_ids)).delete(synchronize_session=False)
            db.query(ReferralAttribution).filter(ReferralAttribution.referral_link_id.in_(link_ids)).delete(synchronize_session=False)
            db.query(ReferralLink).filter(ReferralLink.id.in_(link_ids)).delete(synchronize_session=False)
        if partner_id:
            db.query(ReferralAttribution).filter(ReferralAttribution.partner_id == partner_id).delete(synchronize_session=False)
            db.query(ReferralClick).filter(ReferralClick.partner_id == partner_id).delete(synchronize_session=False)
            db.query(ReferralAuditEvent).filter(ReferralAuditEvent.entity_id == partner_id).delete(synchronize_session=False)
            db.query(ReferralPartner).filter(ReferralPartner.id == partner_id).delete(synchronize_session=False)
        if course_id:
            db.query(Course).filter(Course.id == course_id).delete(synchronize_session=False)
        if user_id:
            db.query(ReferralAuditEvent).filter(ReferralAuditEvent.actor_id == user_id).delete(synchronize_session=False)
            db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
        db.commit()
        db.close()
