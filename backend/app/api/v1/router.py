from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    billing,
    classroom,
    contact,
    events,
    health,
    insights,
    instructors,
    opportunities,
    payments,
    rbac,
    referrals,
    self_paced,
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
api_router.include_router(classroom.router)
api_router.include_router(self_paced.router)
api_router.include_router(events.router)
api_router.include_router(instructors.router)
api_router.include_router(insights.router)
api_router.include_router(opportunities.router)
api_router.include_router(referrals.router)
