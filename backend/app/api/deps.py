from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.rate_limit import RateLimiter
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import get_db
from app.models.user import User
from app.services.auth import AuthService
from app.services.email import EmailService
from app.services.events import EventService
from app.services.google_oauth import GoogleOAuthService
from app.services.admin import AdminService
from app.services.classroom import ClassroomService
from app.services.payments import PaymentService
from app.services.self_paced import SelfPacedService

bearer_scheme = HTTPBearer(auto_error=False)


def get_security_service(settings: Settings = Depends(get_settings)) -> SecurityService:
    return SecurityService(settings)


def get_email_service(settings: Settings = Depends(get_settings)) -> EmailService:
    return EmailService(settings)


def get_google_oauth_service(
    settings: Settings = Depends(get_settings),
) -> GoogleOAuthService:
    return GoogleOAuthService(settings)


def get_rate_limiter(settings: Settings = Depends(get_settings)) -> RateLimiter:
    return RateLimiter(settings)


def get_auth_service(
    db: Session = Depends(get_db),
    security: SecurityService = Depends(get_security_service),
    email_service: EmailService = Depends(get_email_service),
) -> AuthService:
    return AuthService(db, security, email_service)


def get_payment_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    email_service: EmailService = Depends(get_email_service),
) -> PaymentService:
    return PaymentService(db, settings, email_service)


def get_self_paced_service(db: Session = Depends(get_db)) -> SelfPacedService:
    return SelfPacedService(db)


def get_event_service(
    db: Session = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
) -> EventService:
    return EventService(db, email_service)


def get_classroom_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ClassroomService:
    return ClassroomService(db, settings)


def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    return AdminService(db)


def get_current_user(
    db: Session = Depends(get_db),
    security: SecurityService = Depends(get_security_service),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = security.decode_access_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user_optional(
    db: Session = Depends(get_db),
    security: SecurityService = Depends(get_security_service),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User | None:
    if not credentials or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = security.decode_access_token(credentials.credentials)
        if payload.get("type") != "access":
            return None
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
    user = db.get(User, user_id)
    if not user or not user.is_active:
        return None
    return user


def require_roles(*roles: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return dependency


require_admin = require_roles(UserRole.ADMIN)
require_instructor = require_roles(UserRole.ADMIN, UserRole.INSTRUCTOR)
require_event_ops = require_roles(UserRole.ADMIN, UserRole.OPERATIONS)
require_student = require_roles(
    UserRole.ADMIN, UserRole.INSTRUCTOR, UserRole.OPERATIONS, UserRole.STUDENT
)

CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
