from fastapi import APIRouter

from app.api.v1 import admin, auth, classroom, health, payments, rbac, self_paced

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(rbac.router)
api_router.include_router(admin.router)
api_router.include_router(payments.router)
api_router.include_router(classroom.router)
api_router.include_router(self_paced.router)
