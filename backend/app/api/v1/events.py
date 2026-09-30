from __future__ import annotations

import csv
import io
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from app.api.deps import (
    CurrentUser,
    OptionalUser,
    get_event_service,
    get_email_service,
    get_storage_service,
    require_event_ops,
    require_event_registrant_manager,
)
from app.models.user import User
from app.schemas.articles import UploadResponse
from app.schemas.auth import MessageResponse
from app.schemas.events import (
    CheckInResponse,
    EventAdmin,
    EventCardPublic,
    EventCreate,
    EventPublic,
    EventRegistrationPublic,
    EventRegistrantAdmin,
    EventRegistrantEmailRequest,
    EventRegistrantEmailResponse,
    EventUpdate,
    JoinResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services.events import EventService
from app.services.email import EmailService
from app.services.storage import StorageService

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


@router.post("/admin/events/uploads", response_model=UploadResponse)
async def admin_upload_event_image(
    _: User = Depends(require_event_ops),
    storage: StorageService = Depends(get_storage_service),
    file: UploadFile = File(...),
) -> UploadResponse:
    url = await storage.save_image(file)
    return UploadResponse(url=url)


@router.get("/admin/events/{event_id}", response_model=EventAdmin)
def admin_get_event(
    event_id: UUID,
    _: User = Depends(require_event_ops),
    events: EventService = Depends(get_event_service),
) -> EventAdmin:
    return events.get_admin(event_id)


@router.get("/admin/events/{event_id}/registrants", response_model=list[EventRegistrantAdmin])
def admin_event_registrants(
    event_id: UUID,
    _: User = Depends(require_event_registrant_manager),
    events: EventService = Depends(get_event_service),
) -> list[EventRegistrantAdmin]:
    return events.list_admin_registrants(event_id)


@router.get("/admin/events/{event_id}/registrants.csv")
def admin_event_registrants_csv(
    event_id: UUID,
    _: User = Depends(require_event_registrant_manager),
    events: EventService = Depends(get_event_service),
) -> StreamingResponse:
    rows = events.list_admin_registrants(event_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Email", "Phone", "Phone country", "Country of residence", "Status", "Registered at"])
    for row in rows:
        writer.writerow([
            row.full_name or "",
            row.email,
            row.phone_number or "",
            row.phone_country_code or "",
            row.country_of_residence or "",
            row.status,
            row.registered_at.isoformat(),
        ])
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="event-{event_id}-registrants.csv"'},
    )


@router.post("/admin/events/{event_id}/registrants/email", response_model=EventRegistrantEmailResponse)
def admin_email_event_registrants(
    event_id: UUID,
    payload: EventRegistrantEmailRequest,
    _: User = Depends(require_event_registrant_manager),
    events: EventService = Depends(get_event_service),
    email_service: EmailService = Depends(get_email_service),
) -> EventRegistrantEmailResponse:
    event = events._get_by_id(event_id)
    rows = events.list_admin_registrants(event_id)
    selected = set(payload.recipient_user_ids)
    recipients = [row for row in rows if row.status == "registered" and (not selected or row.user_id in selected)]
    event_link = f"{email_service.settings.frontend_url.rstrip('/')}/events/{event.slug}" if payload.include_event_link else None
    sent = 0
    failed = 0
    for row in recipients:
        if email_service.send_event_registrant_message(
            email=row.email,
            full_name=row.full_name,
            subject=payload.subject.strip(),
            message=payload.message.strip(),
            event_title=event.title,
            event_link=event_link,
        ):
            sent += 1
        else:
            failed += 1
    return EventRegistrantEmailResponse(sent=sent, failed=failed)


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
