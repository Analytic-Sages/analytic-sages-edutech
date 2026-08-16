from fastapi import APIRouter, Depends

from app.api.deps import require_admin, require_instructor
from app.models.user import User
from app.schemas.auth import MessageResponse

router = APIRouter(tags=["rbac"])


@router.get("/admin/ping", response_model=MessageResponse)
def admin_ping(current_user: User = Depends(require_admin)) -> MessageResponse:
    return MessageResponse(message=f"Admin access granted for {current_user.email}")


@router.get("/instructor/ping", response_model=MessageResponse)
def instructor_ping(current_user: User = Depends(require_instructor)) -> MessageResponse:
    return MessageResponse(message=f"Instructor access granted for {current_user.email}")
