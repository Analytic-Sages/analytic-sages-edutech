from __future__ import annotations

from uuid import UUID

import hmac

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import (
    CurrentUser,
    bearer_scheme,
    get_classroom_service,
    get_security_service,
)
from app.core.config import Settings, get_settings
from app.core.security import SecurityService
from app.db.session import get_db
from app.models.user import User
from app.schemas.classroom import (
    ClassroomCalendarFeed,
    ClassroomJoinResponse,
    LiveSessionPublic,
    PublicCohortCard,
)
from app.services.classroom import ClassroomService
from app.services.seed_bde_classroom import seed_bde_classroom

router = APIRouter(prefix="/classroom", tags=["classroom"])
# Token-protected ops hooks, mounted at /api/v1/internal/* (mirrors billing.admin_router).
internal_router = APIRouter(tags=["internal"])


def _resolve_feed_user(
    *,
    db: Session,
    security: SecurityService,
    credentials: HTTPAuthorizationCredentials | None,
    token: str | None,
) -> User:
    """Authenticate a calendar feed request via bearer header or ?token= query.

    Calendar subscriptions cannot send an Authorization header, so the URL carries
    a signed feed token. Either credential maps to the same authorization rules.
    """
    user: User | None = None
    if credentials and credentials.scheme.lower() == "bearer":
        try:
            payload = security.decode_access_token(credentials.credentials)
            if payload.get("type") == "access":
                user = db.get(User, UUID(payload["sub"]))
        except (jwt.PyJWTError, KeyError, ValueError):
            user = None

    if user is None and token:
        try:
            user = db.get(User, UUID(security.decode_calendar_feed_token(token)))
        except (jwt.PyJWTError, KeyError, ValueError):
            user = None

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.get("/public/cohorts", response_model=list[PublicCohortCard])
def list_public_cohorts(
    classroom: ClassroomService = Depends(get_classroom_service),
) -> list[PublicCohortCard]:
    """Public Instructor-Led catalog (no auth)."""
    return classroom.list_public_cohorts()


@router.get("/sessions", response_model=list[LiveSessionPublic])
def list_my_sessions(
    current_user: CurrentUser,
    classroom: ClassroomService = Depends(get_classroom_service),
) -> list[LiveSessionPublic]:
    return classroom.list_my_sessions(current_user)


@router.get("/sessions/{session_id}", response_model=LiveSessionPublic)
def get_session(
    session_id: UUID,
    current_user: CurrentUser,
    classroom: ClassroomService = Depends(get_classroom_service),
) -> LiveSessionPublic:
    return classroom.get_session_for_user(current_user, session_id)


@router.post("/sessions/{session_id}/join", response_model=ClassroomJoinResponse)
def join_session(
    session_id: UUID,
    current_user: CurrentUser,
    classroom: ClassroomService = Depends(get_classroom_service),
) -> ClassroomJoinResponse:
    return classroom.join_session(current_user, session_id)


@router.get("/calendar-token", response_model=ClassroomCalendarFeed)
def classroom_calendar_token(
    current_user: CurrentUser,
    settings: Settings = Depends(get_settings),
    security: SecurityService = Depends(get_security_service),
) -> ClassroomCalendarFeed:
    """Personal subscribe URL for the classroom calendar (Google/Apple/Outlook)."""
    token = security.create_calendar_feed_token(user_id=str(current_user.id))
    base = str(settings.public_api_url).rstrip("/")
    url = f"{base}/api/v1/classroom/calendar.ics?token={token}"
    return ClassroomCalendarFeed(
        token=token,
        url=url,
        webcal_url=url.replace("https://", "webcal://", 1).replace("http://", "webcal://", 1),
    )


@router.get("/calendar.ics")
def classroom_calendar_feed(
    token: str | None = Query(default=None, description="Signed calendar feed token"),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    security: SecurityService = Depends(get_security_service),
) -> Response:
    """iCalendar feed of the user's classroom sessions, with reminders.

    Accepts either the normal bearer token (in-app download) or a signed ``?token=``
    so calendar apps can subscribe and keep receiving schedule updates.
    """
    user = _resolve_feed_user(db=db, security=security, credentials=credentials, token=token)
    classroom = ClassroomService(db, settings)
    ics = classroom.calendar_ics(user)
    return Response(
        content=ics,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": 'inline; filename="analytic-sages-classroom.ics"',
            "Cache-Control": "no-store",
        },
    )


@internal_router.post("/internal/classroom/sync-schedule")
def internal_sync_classroom_schedule(
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
    x_classroom_sync_token: str | None = Header(default=None),
) -> dict[str, int]:
    """Cron/ops hook: re-provision the canonical classroom schedule for every cohort.

    Idempotent — it creates/updates the 30-session Blockchain Data Engineering plan
    (20 teaching sessions Mon/Wed + 10 Friday office hours) and collapses any
    stale placeholder rows, so a deployment can guarantee the *complete* schedule
    exists without running a seed script by hand.

    Token-protected (CLASSROOM_SYNC_TOKEN, falling back to OPPORTUNITY_SYNC_TOKEN).
    """
    expected = (settings.classroom_sync_token or settings.opportunity_sync_token or "").strip()
    if not expected:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    provided = (x_classroom_sync_token or "").strip()
    if len(provided) != len(expected) or not hmac.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid classroom sync token"
        )
    return seed_bde_classroom(db)
