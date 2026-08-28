from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.admin import FEATURED_COHORT_SLUG
from app.core.payments import EnrollmentStatus, PaymentStatus
from app.core.roles import UserRole
from app.models.article import Article, ArticleStatus
from app.models.classroom import Cohort, CohortMember, CohortMemberRole, CohortStatus
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.event import EventRegistration, EventRegistrationStatus
from app.models.lms import LessonProgress
from app.models.opportunity import Opportunity, OpportunityStatus, OpportunitySave
from app.models.payment import Payment
from app.models.user import User
from app.schemas.admin import (
    AdminAnalytics,
    AdminCohortDetail,
    AdminCohortMemberRow,
    AdminCountPoint,
    AdminFeaturedCohort,
    AdminNamedCount,
    AdminOverview,
    AdminPaymentRow,
    AdminRecentLearner,
    AdminRevenueByCurrency,
    AdminUserRow,
)

PENDING_STATUSES = (PaymentStatus.PENDING, PaymentStatus.CONFIRMING)
LIST_CAP = 500
ANALYTICS_DAYS = 30
UNTRACKED = [
    "Watch time is not recorded.",
    "Quiz attempts and pass rates are not tracked yet.",
    "Last login is not stored; recent learners use last lesson activity only.",
    "Certificate issuance is not live.",
]


class AdminService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def overview(self) -> AdminOverview:
        now = datetime.now(UTC)
        featured = self._featured_cohort()
        featured_member_ids = self._member_user_ids(featured.id) if featured else set()

        users_total = self._count(User)
        students_total = self._count(User, User.role == UserRole.STUDENT)
        users_verified = self._count(User, User.email_verified.is_(True))
        signups_24h = self._count(User, User.created_at >= now - timedelta(hours=24))
        signups_7d = self._count(User, User.created_at >= now - timedelta(days=7))
        payments_confirmed = self._count(Payment, Payment.status == PaymentStatus.CONFIRMED)
        payments_pending = self._count(Payment, Payment.status.in_(PENDING_STATUSES))

        return AdminOverview(
            users_total=users_total,
            students_total=students_total,
            users_verified=users_verified,
            signups_24h=signups_24h,
            signups_7d=signups_7d,
            payments_confirmed=payments_confirmed,
            payments_pending=payments_pending,
            revenue_by_currency=self._revenue_by_currency(),
            featured_cohort=self._cohort_summary(featured) if featured else None,
            recent_signups=self._user_rows(self._list_users(limit=8), featured_member_ids),
            recent_payments=self._payment_rows(self._list_payments(limit=8)),
        )

    def analytics(self) -> AdminAnalytics:
        now = datetime.now(UTC)
        featured = self._featured_cohort()
        users_total = self._count(User)
        users_verified = self._count(User, User.email_verified.is_(True))

        return AdminAnalytics(
            users_total=users_total,
            students_total=self._count(User, User.role == UserRole.STUDENT),
            users_verified=users_verified,
            users_unverified=max(users_total - users_verified, 0),
            signups_24h=self._count(User, User.created_at >= now - timedelta(hours=24)),
            signups_7d=self._count(User, User.created_at >= now - timedelta(days=7)),
            signups_30d=self._count(User, User.created_at >= now - timedelta(days=30)),
            enrollments_active=self._count(Enrollment, Enrollment.status == EnrollmentStatus.ACTIVE),
            enrollments_completed=self._count(
                Enrollment, Enrollment.status == EnrollmentStatus.COMPLETED
            ),
            lessons_completed=self._count(LessonProgress, LessonProgress.completed.is_(True)),
            learners_active_7d=int(
                self.db.scalar(
                    select(func.count(func.distinct(Enrollment.user_id))).where(
                        Enrollment.last_activity_at >= now - timedelta(days=7)
                    )
                )
                or 0
            ),
            payments_confirmed=self._count(Payment, Payment.status == PaymentStatus.CONFIRMED),
            payments_pending=self._count(Payment, Payment.status.in_(PENDING_STATUSES)),
            event_registrations=self._count(
                EventRegistration,
                EventRegistration.status == EventRegistrationStatus.REGISTERED,
            ),
            published_opportunities=self._count(
                Opportunity, Opportunity.status == OpportunityStatus.PUBLISHED
            ),
            opportunity_saves=self._count(OpportunitySave),
            published_insights=self._count(Article, Article.status == ArticleStatus.PUBLISHED),
            revenue_by_currency=self._revenue_by_currency(),
            featured_cohort=self._cohort_summary(featured) if featured else None,
            signups_by_day=self._daily_counts(User.created_at),
            enrollments_by_day=self._daily_counts(Enrollment.enrolled_at),
            roles=self._enum_counts(User.role, [role.value for role in UserRole]),
            courses=self._course_enrollment_counts(),
            opportunity_statuses=self._enum_counts(
                Opportunity.status, [status.value for status in OpportunityStatus]
            ),
            recent_learners=self._recent_learners(),
            untracked=list(UNTRACKED),
        )

    def list_users(self, *, limit: int = 200) -> list[AdminUserRow]:
        featured = self._featured_cohort()
        member_ids = self._member_user_ids(featured.id) if featured else set()
        return self._user_rows(self._list_users(limit=limit), member_ids)

    def list_payments(self, *, limit: int = 200) -> list[AdminPaymentRow]:
        return self._payment_rows(self._list_payments(limit=limit))

    def cohort_detail(self, slug: str) -> AdminCohortDetail:
        cohort = self.db.scalar(select(Cohort).where(Cohort.slug == slug))
        if not cohort:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")

        members = list(
            self.db.scalars(
                select(CohortMember)
                .options(joinedload(CohortMember.user))
                .where(CohortMember.cohort_id == cohort.id)
                .order_by(CohortMember.joined_at.desc())
            ).unique()
        )
        payments = self._list_payments(limit=LIST_CAP, cohort_id=cohort.id)
        return AdminCohortDetail(
            cohort=self._cohort_summary(cohort),
            members=[self._member_row(member) for member in members],
            payments=self._payment_rows(payments),
        )

    def add_instructor_to_featured_cohort(self, user: User) -> None:
        cohort = self._featured_cohort()
        if not cohort:
            return
        existing = self.db.scalar(
            select(CohortMember).where(
                CohortMember.cohort_id == cohort.id,
                CohortMember.user_id == user.id,
            )
        )
        if existing:
            if existing.role == CohortMemberRole.STUDENT:
                existing.role = CohortMemberRole.INSTRUCTOR
            return
        self.db.add(
            CohortMember(
                cohort_id=cohort.id,
                user_id=user.id,
                role=CohortMemberRole.INSTRUCTOR,
            )
        )
        self.db.commit()

    def _featured_cohort(self) -> Cohort | None:
        cohort = self.db.scalar(select(Cohort).where(Cohort.slug == FEATURED_COHORT_SLUG))
        if cohort:
            return cohort
        return self.db.scalar(
            select(Cohort)
            .where(Cohort.status.in_((CohortStatus.OPEN, CohortStatus.ACTIVE)))
            .order_by(Cohort.starts_at.desc().nulls_last())
            .limit(1)
        )

    def _count(self, model: type, *filters: object) -> int:
        stmt = select(func.count()).select_from(model)
        if filters:
            stmt = stmt.where(*filters)  # type: ignore[arg-type]
        return int(self.db.scalar(stmt) or 0)

    def _member_user_ids(self, cohort_id: UUID) -> set[UUID]:
        return set(
            self.db.scalars(select(CohortMember.user_id).where(CohortMember.cohort_id == cohort_id)).all()
        )

    def _list_users(self, *, limit: int) -> list[User]:
        return list(
            self.db.scalars(
                select(User).order_by(User.created_at.desc()).limit(self._clamp(limit))
            ).all()
        )

    def _list_payments(self, *, limit: int, cohort_id: UUID | None = None) -> list[Payment]:
        stmt = (
            select(Payment)
            .options(
                joinedload(Payment.user),
                joinedload(Payment.cohort),
                joinedload(Payment.course),
            )
            .order_by(Payment.created_at.desc())
            .limit(self._clamp(limit))
        )
        if cohort_id:
            stmt = stmt.where(Payment.cohort_id == cohort_id)
        return list(self.db.scalars(stmt).unique().all())

    def _user_rows(self, users: list[User], member_ids: set[UUID]) -> list[AdminUserRow]:
        return [
            AdminUserRow(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                email_verified=user.email_verified,
                is_active=user.is_active,
                in_featured_cohort=user.id in member_ids,
                created_at=user.created_at,
            )
            for user in users
        ]

    def _payment_rows(self, payments: list[Payment]) -> list[AdminPaymentRow]:
        rows: list[AdminPaymentRow] = []
        for payment in payments:
            rows.append(
                AdminPaymentRow(
                    id=payment.id,
                    order_id=payment.order_id,
                    status=payment.status.value,
                    provider=payment.provider.value,
                    amount=payment.amount,
                    currency=payment.currency,
                    user_email=payment.user.email if payment.user else "",
                    user_name=payment.user.full_name if payment.user else None,
                    cohort_name=payment.cohort.name if payment.cohort else None,
                    course_title=payment.course.title if payment.course else None,
                    confirmed_at=payment.confirmed_at,
                    created_at=payment.created_at,
                )
            )
        return rows

    def _member_row(self, member: CohortMember) -> AdminCohortMemberRow:
        user = member.user
        return AdminCohortMemberRow(
            id=member.id,
            user_id=member.user_id,
            email=user.email if user else "",
            full_name=user.full_name if user else None,
            role=member.role.value,
            email_verified=bool(user.email_verified) if user else False,
            joined_at=member.joined_at,
        )

    def _cohort_summary(self, cohort: Cohort) -> AdminFeaturedCohort:
        student_seats = self._count(
            CohortMember,
            CohortMember.cohort_id == cohort.id,
            CohortMember.role == CohortMemberRole.STUDENT,
        )
        staff_count = self._count(
            CohortMember,
            CohortMember.cohort_id == cohort.id,
            CohortMember.role.in_((CohortMemberRole.INSTRUCTOR, CohortMemberRole.TA)),
        )
        confirmed_payments = self._count(
            Payment,
            Payment.cohort_id == cohort.id,
            Payment.status == PaymentStatus.CONFIRMED,
        )
        pending_payments = self._count(
            Payment,
            Payment.cohort_id == cohort.id,
            Payment.status.in_(PENDING_STATUSES),
        )
        return AdminFeaturedCohort(
            id=cohort.id,
            name=cohort.name,
            slug=cohort.slug,
            status=cohort.status.value,
            price=cohort.price,
            currency=cohort.currency,
            student_seats=student_seats,
            staff_count=staff_count,
            confirmed_payments=confirmed_payments,
            pending_payments=pending_payments,
            registration_deadline=cohort.registration_deadline,
            starts_at=cohort.starts_at,
        )

    def _revenue_by_currency(self) -> list[AdminRevenueByCurrency]:
        rows = self.db.execute(
            select(
                Payment.currency,
                Payment.status,
                func.coalesce(func.sum(Payment.amount), 0),
            ).group_by(Payment.currency, Payment.status)
        ).all()
        totals: dict[str, AdminRevenueByCurrency] = {}
        for currency, pay_status, amount in rows:
            bucket = totals.setdefault(
                currency,
                AdminRevenueByCurrency(currency=currency, confirmed_amount=0, pending_amount=0),
            )
            value = int(amount or 0)
            if pay_status == PaymentStatus.CONFIRMED:
                bucket.confirmed_amount += value
            elif pay_status in PENDING_STATUSES:
                bucket.pending_amount += value
        return sorted(totals.values(), key=lambda item: item.currency)

    def _daily_counts(self, column: object, *filters: object) -> list[AdminCountPoint]:
        now = datetime.now(UTC)
        start = datetime(now.year, now.month, now.day, tzinfo=UTC) - timedelta(
            days=ANALYTICS_DAYS - 1
        )
        day_expr = func.date_trunc("day", column)
        stmt = select(day_expr, func.count()).where(column >= start)
        if filters:
            stmt = stmt.where(*filters)  # type: ignore[arg-type]
        rows = self.db.execute(stmt.group_by(day_expr).order_by(day_expr)).all()
        counts: dict[str, int] = {}
        for day, value in rows:
            if day is None:
                continue
            if getattr(day, "tzinfo", None) is None:
                day = day.replace(tzinfo=UTC)
            else:
                day = day.astimezone(UTC)
            counts[day.date().isoformat()] = int(value or 0)
        return [
            AdminCountPoint(
                label=(start + timedelta(days=offset)).date().isoformat(),
                value=counts.get((start + timedelta(days=offset)).date().isoformat(), 0),
            )
            for offset in range(ANALYTICS_DAYS)
        ]

    def _enum_counts(self, column: object, names: list[str]) -> list[AdminNamedCount]:
        rows = self.db.execute(select(column, func.count()).group_by(column)).all()
        found: dict[str, int] = {}
        for name, value in rows:
            key = name.value if hasattr(name, "value") else str(name)
            found[key] = int(value or 0)
        return [AdminNamedCount(name=name, value=found.get(name, 0)) for name in names]

    def _course_enrollment_counts(self) -> list[AdminNamedCount]:
        rows = self.db.execute(
            select(Course.title, func.count())
            .join(Enrollment, Enrollment.course_id == Course.id)
            .where(
                Enrollment.status.in_((EnrollmentStatus.ACTIVE, EnrollmentStatus.COMPLETED))
            )
            .group_by(Course.title)
            .order_by(func.count().desc())
            .limit(8)
        ).all()
        return [AdminNamedCount(name=title, value=int(count or 0)) for title, count in rows]

    def _recent_learners(self) -> list[AdminRecentLearner]:
        enrollments = list(
            self.db.scalars(
                select(Enrollment)
                .options(joinedload(Enrollment.user), joinedload(Enrollment.course))
                .where(Enrollment.last_activity_at.is_not(None))
                .order_by(Enrollment.last_activity_at.desc())
                .limit(8)
            )
            .unique()
            .all()
        )
        rows: list[AdminRecentLearner] = []
        for enrollment in enrollments:
            if enrollment.last_activity_at is None:
                continue
            user = enrollment.user
            course = enrollment.course
            rows.append(
                AdminRecentLearner(
                    user_email=user.email if user else "",
                    user_name=user.full_name if user else None,
                    course_title=course.title if course else "",
                    last_activity_at=enrollment.last_activity_at,
                )
            )
        return rows

    @staticmethod
    def _clamp(limit: int) -> int:
        return max(1, min(limit, LIST_CAP))
