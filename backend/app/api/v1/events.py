from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, OptionalUser, get_event_service, require_event_ops
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.events import (
    CheckInResponse,
    EventAdmin,
    EventCardPublic,
    EventCreate,
    EventPublic,
    EventRegistrationPublic,
    EventUpdate,
    JoinResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services.events import EventService

router = APIRouter(tags=["events"])


@router.get("/events", response_model=list[EventCardPublic])
def list_events(
    current_user: OptionalUser,
    events: EventService = Depends(get_event_service),
    upcoming: bool = Query(default=False),
    limit: int | None = Query(default=None, ge=1, le=50),
) -> list[EventCardPublic]:
    return events.list_public(current_user, upcoming_only=upcoming, limit=limit)


@router.get("/events/me", response_model=list[EventRegistrationPublic])
def my_events(
    current_user: CurrentUser,
    events: EventService = Depends(get_event_service),
) -> list[EventRegistrationPublic]:
    return events.list_mine(current_user)


@router.get("/events/{slug}", response_model=EventPublic)
def get_event(
    slug: str,
    current_user: OptionalUser,
    events: EventService = Depends(get_event_service),
) -> EventPublic:
    return events.get_public(slug, current_user)


@router.post("/events/{slug}/register", response_model=RegisterResponse)
def register_for_event(
    slug: str,
    current_user: CurrentUser,
    events: EventService = Depends(get_event_service),
    payload: RegisterRequest = RegisterRequest(),
) -> RegisterResponse:
    return events.register(current_user, slug, source=payload.source)


@router.delete("/events/{slug}/register", response_model=MessageResponse)
def cancel_event_registration(
    slug: str,
    current_user: CurrentUser,
    events: EventService = Depends(get_event_service),
) -> MessageResponse:
    events.cancel_registration(current_user, slug)
    return MessageResponse(message="Registration cancelled.")


@router.post("/events/{slug}/join", response_model=JoinResponse)
def join_event(
    slug: str,
    current_user: CurrentUser,
    events: EventService = Depends(get_event_service),
) -> JoinResponse:
    return events.join(current_user, slug)


@router.post("/events/{slug}/check-in", response_model=CheckInResponse)
def check_in_event(
    slug: str,
    current_user: CurrentUser,
    events: EventService = Depends(get_event_service),
) -> CheckInResponse:
    return events.check_in(current_user, slug)


@router.get("/admin/events", response_model=list[EventAdmin])
def admin_list_events(
    _: User = Depends(require_event_ops),
    events: EventService = Depends(get_event_service),
) -> list[EventAdmin]:
    return events.list_admin()


@router.post("/admin/events", response_model=EventAdmin, status_code=status.HTTP_201_CREATED)
def admin_create_event(
    payload: EventCreate,
    current_user: User = Depends(require_event_ops),
    events: EventService = Depends(get_event_service),
) -> EventAdmin:
    return events.create(payload, host=current_user)


@router.get("/admin/events/{event_id}", response_model=EventAdmin)
def admin_get_event(
    event_id: UUID,
    _: User = Depends(require_event_ops),
    events: EventService = Depends(get_event_service),
) -> EventAdmin:
    return events.get_admin(event_id)


@router.patch("/admin/events/{event_id}", response_model=EventAdmin)
def admin_update_event(
    event_id: UUID,
    payload: EventUpdate,
    _: User = Depends(require_event_ops),
    events: EventService = Depends(get_event_service),
) -> EventAdmin:
    return events.update(event_id, payload)


@router.post("/admin/events/{event_id}/cancel", response_model=EventAdmin)
def admin_cancel_event(
    event_id: UUID,
    _: User = Depends(require_event_ops),
    events: EventService = Depends(get_event_service),
) -> EventAdmin:
    return events.update(event_id, EventUpdate(cancelled=True))
