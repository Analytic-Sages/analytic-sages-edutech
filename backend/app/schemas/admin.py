from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminUserRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None
    role: str
    email_verified: bool
    is_active: bool
    in_featured_cohort: bool = False
    created_at: datetime


class AdminPaymentRow(BaseModel):
    id: UUID
    order_id: str
    status: str
    provider: str
    amount: int
    currency: str
    user_email: str
    user_name: str | None
    cohort_name: str | None
    course_title: str | None
    confirmed_at: datetime | None
    created_at: datetime


class AdminCohortMemberRow(BaseModel):
    id: UUID
    user_id: UUID
    email: EmailStr
    full_name: str | None
    role: str
    email_verified: bool
    joined_at: datetime


class AdminRevenueByCurrency(BaseModel):
    currency: str
    confirmed_amount: int
    pending_amount: int


class AdminFeaturedCohort(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    price: int
    currency: str
    student_seats: int
    staff_count: int
    confirmed_payments: int
    pending_payments: int
    registration_deadline: datetime | None
    starts_at: datetime | None


class AdminOverview(BaseModel):
    users_total: int
    students_total: int
    users_verified: int
    signups_24h: int
    signups_7d: int
    payments_confirmed: int
    payments_pending: int
    revenue_by_currency: list[AdminRevenueByCurrency]
    featured_cohort: AdminFeaturedCohort | None
    recent_signups: list[AdminUserRow]
    recent_payments: list[AdminPaymentRow]


class AdminCountPoint(BaseModel):
    label: str
    value: int


class AdminNamedCount(BaseModel):
    name: str
    value: int


class AdminRecentLearner(BaseModel):
    user_email: str
    user_name: str | None
    course_title: str
    last_activity_at: datetime


class AdminAnalytics(BaseModel):
    users_total: int
    students_total: int
    users_verified: int
    users_unverified: int
    signups_24h: int
    signups_7d: int
    signups_30d: int
    enrollments_active: int
    enrollments_completed: int
    lessons_completed: int
    learners_active_7d: int
    payments_confirmed: int
    payments_pending: int
    event_registrations: int
    published_opportunities: int
    opportunity_saves: int
    published_insights: int
    revenue_by_currency: list[AdminRevenueByCurrency]
    featured_cohort: AdminFeaturedCohort | None
    signups_by_day: list[AdminCountPoint]
    enrollments_by_day: list[AdminCountPoint]
    roles: list[AdminNamedCount]
    courses: list[AdminNamedCount]
    opportunity_statuses: list[AdminNamedCount]
    recent_learners: list[AdminRecentLearner]
    untracked: list[str]


class AdminCohortDetail(BaseModel):
    cohort: AdminFeaturedCohort
    members: list[AdminCohortMemberRow]
    payments: list[AdminPaymentRow]


class InviteInstructorRequest(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=255)


class InviteInstructorResponse(BaseModel):
    email: EmailStr
    full_name: str | None
    role: str
    resent: bool
    promoted: bool = False
    message: str
