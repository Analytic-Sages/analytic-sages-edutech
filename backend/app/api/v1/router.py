from fastapi import APIRouter

from app.api.v1 import auth, classroom, health, payments, rbac

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(rbac.router)
api_router.include_router(payments.router)
api_router.include_router(classroom.router)
