from fastapi import APIRouter

from app.api.v1 import (
    admin,
    assignments,
    auth,
    billing,
    classroom,
    contact,
    events,
    experience,
    health,
    insights,
    instructors,
    live,
    opportunities,
    payments,
    projects,
    quizzes,
    rbac,
    realtimekit_webhooks,
    referrals,
    self_paced,
    waitlist,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(contact.router)
api_router.include_router(auth.router)
api_router.include_router(rbac.router)
api_router.include_router(admin.router)
api_router.include_router(billing.router)
api_router.include_router(billing.admin_router)
api_router.include_router(payments.router)
api_router.include_router(realtimekit_webhooks.router)
api_router.include_router(classroom.router)
api_router.include_router(classroom.internal_router)
api_router.include_router(assignments.router)
api_router.include_router(projects.router)
api_router.include_router(experience.router)
api_router.include_router(self_paced.router)
api_router.include_router(quizzes.router)
api_router.include_router(events.router)
api_router.include_router(instructors.router)
api_router.include_router(live.router)
api_router.include_router(waitlist.router)
api_router.include_router(insights.router)
api_router.include_router(opportunities.router)
api_router.include_router(referrals.router)
