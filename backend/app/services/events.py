from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.event import Event, EventPlatform, EventRegistration, EventRegistrationStatus, EventType
from app.models.user import User
from app.schemas.events import (
    CheckInResponse,
    EventAdmin,
    EventCardPublic,
    EventCreate,
    EventPublic,
    EventRegistrationPublic,
    EventUpdate,
    JoinResponse,
    RegisterResponse,
    normalize_keep_learning,
    platform_display_name,
)
from app.services.email import EmailService

JOIN_WINDOW = timedelta(minutes=15)


class EventService:
    def __init__(self, db: Session, email_service: EmailService | None = None) -> None:
        self.db = db
        self.email_service = email_service

    def _utcnow(self) -> datetime:
        return datetime.now(UTC)

    def _aware(self, value: datetime, timezone_name: str) -> datetime:
        if value.tzinfo is None:
            try:
                zone = ZoneInfo(timezone_name)
            except ZoneInfoNotFoundError:
                zone = UTC
            return value.replace(tzinfo=zone).astimezone(UTC)
        return value.astimezone(UTC)

    def _as_str_list(self, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    def _registered_count(self, event_id: UUID) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(EventRegistration)
                .where(
                    EventRegistration.event_id == event_id,
                    EventRegistration.status == EventRegistrationStatus.REGISTERED,
                )
            )
            or 0
        )

    def _registration_for(self, user: User | None, event_id: UUID) -> EventRegistration | None:
        if not user:
            return None
        return self.db.scalar(
            select(EventRegistration).where(
                EventRegistration.user_id == user.id,
                EventRegistration.event_id == event_id,
            )
        )

    def _active_registration(self, user: User | None, event_id: UUID) -> EventRegistration | None:
        row = self._registration_for(user, event_id)
        if row and row.status == EventRegistrationStatus.REGISTERED:
            return row
        return None

    def _utc(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def compute_lifecycle(self, event: Event, now: datetime | None = None) -> str:
        current = now or self._utcnow()
        if event.cancelled:
            return "cancelled"
        if not event.published:
            return "draft"
        starts_at = self._utc(event.starts_at)
        ends_at = self._utc(event.ends_at)
        if starts_at is None or ends_at is None:
            return "coming_soon"
        if current >= ends_at:
            return "completed"
        if current >= starts_at:
            return "live"
        deadline = self._utc(event.registration_deadline)
        if deadline is not None and current >= deadline:
            return "registration_closed"
        return "upcoming"

    def _can_register(self, event: Event, user: User | None, now: datetime) -> bool:
        lifecycle = self.compute_lifecycle(event, now)
        if lifecycle in {"cancelled", "draft", "completed", "coming_soon"}:
            return False
        if event.price > 0:
            return False
        if self._active_registration(user, event.id):
            return False
        if event.capacity is not None and self._registered_count(event.id) >= event.capacity:
            return False
        if lifecycle == "registration_closed":
            return False
        return True

    def _can_join(self, event: Event, user: User | None, now: datetime) -> bool:
        if not self._active_registration(user, event.id):
            return False
        lifecycle = self.compute_lifecycle(event, now)
        if lifecycle in {"cancelled", "draft", "completed", "coming_soon"}:
            return False
        starts_at = self._utc(event.starts_at)
        if starts_at is None:
            return False
        return now >= (starts_at - JOIN_WINDOW) and bool(event.youtube_live_url)

    def _can_watch_recording(self, event: Event, user: User | None) -> bool:
        if not event.recording_url or not event.published or event.cancelled:
            return False
        # Free events: once a recording URL is set, it is publicly watchable.
        if event.price == 0:
            return True
        if not self._active_registration(user, event.id):
            return False
        lifecycle = self.compute_lifecycle(event)
        return lifecycle in {"completed", "live"}

    def _platform_value(self, event: Event) -> str:
        return (event.platform or EventPlatform.YOUTUBE.value).strip().lower()

    def _card(self, event: Event, user: User | None, now: datetime | None = None) -> EventCardPublic:
        current = now or self._utcnow()
        platform = self._platform_value(event)
        return EventCardPublic(
            id=event.id,
            slug=event.slug,
            title=event.title,
            event_type=event.event_type.value if isinstance(event.event_type, EventType) else str(event.event_type),
            short_description=event.short_description,
            cover_image=event.cover_image,
            starts_at=event.starts_at,
            ends_at=event.ends_at,
            timezone=event.timezone,
            price=event.price,
            currency=event.currency,
            is_free=event.price == 0,
            host_name=event.host_name,
            platform=platform,
            platform_label=event.platform_label,
            platform_display=platform_display_name(platform, event.platform_label),
            lifecycle=self.compute_lifecycle(event, current),
            registered=self._active_registration(user, event.id) is not None,
            can_register=self._can_register(event, user, current),
            related_course_slug=event.related_course_slug,
            has_recording=bool(event.recording_url),
        )

    def _keep_learning(self, event: Event) -> list[dict[str, str]]:
        offers = normalize_keep_learning(event.keep_learning)
        if offers:
            return offers
        if event.related_course_slug:
            return [{"kind": "course", "slug": event.related_course_slug}]
        return []

    def _related_slug_from_keep_learning(self, offers: list[dict[str, str]]) -> str | None:
        for offer in offers:
            if offer.get("kind") == "course":
                return offer.get("slug")
        return None

    def _public(self, event: Event, user: User | None) -> EventPublic:
        now = self._utcnow()
        registered = self._active_registration(user, event.id) is not None
        can_watch = self._can_watch_recording(event, user)
        card = self._card(event, user, now)
        return EventPublic(
            **card.model_dump(),
            description=event.description,
            learn_topics=self._as_str_list(event.learn_topics),
            audience=self._as_str_list(event.audience),
            prerequisites=event.prerequisites or "",
            registration_deadline=event.registration_deadline,
            capacity=event.capacity,
            cancelled=event.cancelled,
            can_join=self._can_join(event, user, now),
            can_watch_recording=can_watch,
            youtube_live_url=event.youtube_live_url if registered else None,
            recording_url=event.recording_url if can_watch else None,
            keep_learning=self._keep_learning(event),
            seo_title=event.seo_title,
            seo_description=event.seo_description,
        )

    def _admin(self, event: Event) -> EventAdmin:
        platform = self._platform_value(event)
        return EventAdmin(
            id=event.id,
            slug=event.slug,
            title=event.title,
            event_type=event.event_type.value if isinstance(event.event_type, EventType) else str(event.event_type),
            short_description=event.short_description,
            description=event.description,
            cover_image=event.cover_image,
            starts_at=event.starts_at,
            ends_at=event.ends_at,
            timezone=event.timezone,
            price=event.price,
            currency=event.currency,
            registration_deadline=event.registration_deadline,
            capacity=event.capacity,
            host_name=event.host_name,
            platform=platform,
            platform_label=event.platform_label,
            platform_display=platform_display_name(platform, event.platform_label),
            youtube_live_url=event.youtube_live_url,
            recording_url=event.recording_url,
            learn_topics=self._as_str_list(event.learn_topics),
            audience=self._as_str_list(event.audience),
            prerequisites=event.prerequisites or "",
            related_course_slug=event.related_course_slug,
            keep_learning=self._keep_learning(event),
            seo_title=event.seo_title,
            seo_description=event.seo_description,
            published=event.published,
            cancelled=event.cancelled,
            lifecycle=self.compute_lifecycle(event),
            registered_count=self._registered_count(event.id),
            created_at=event.created_at,
            updated_at=event.updated_at,
        )

    def _published_event(self, slug: str) -> Event:
        event = self.db.scalar(select(Event).where(Event.slug == slug, Event.published.is_(True)))
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return event

    def _get_by_id(self, event_id: UUID) -> Event:
        event = self.db.get(Event, event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return event

    def list_public(
        self,
        user: User | None,
        *,
        upcoming_only: bool = False,
        limit: int | None = None,
    ) -> list[EventCardPublic]:
        now = self._utcnow()
        query = select(Event).where(Event.published.is_(True), Event.cancelled.is_(False))
        if upcoming_only:
            query = query.where(or_(Event.starts_at.is_(None), Event.ends_at >= now)).order_by(
                Event.starts_at.asc().nulls_first()
            )
        else:
            query = query.order_by(Event.starts_at.desc().nulls_first())
        if limit:
            query = query.limit(limit)
        return [self._card(event, user, now) for event in self.db.scalars(query).all()]

    def get_public(self, slug: str, user: User | None) -> EventPublic:
        return self._public(self._published_event(slug), user)

    def register(self, user: User, slug: str, source: str | None = None) -> RegisterResponse:
        event = self._published_event(slug)
        now = self._utcnow()
        existing = self._registration_for(user, event.id)
        if existing and existing.status == EventRegistrationStatus.REGISTERED:
            return RegisterResponse(
                registration_id=existing.id,
                event_slug=event.slug,
                already_registered=True,
                status=existing.status.value,
            )
        if not self._can_register(event, user, now):
            lifecycle = self.compute_lifecycle(event, now)
            if lifecycle == "cancelled":
                detail = "This event has been cancelled"
            elif lifecycle == "coming_soon":
                detail = "This event is coming soon. Registration opens when a date is announced."
            elif lifecycle == "completed":
                detail = "This event has already ended"
            elif lifecycle == "registration_closed":
                detail = "Registration for this event is closed"
            elif event.price > 0:
                detail = "Paid events are not available yet"
            elif event.capacity is not None and self._registered_count(event.id) >= event.capacity:
                detail = "This event is full"
            else:
                detail = "You cannot register for this event"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

        already = False
        if existing:
            existing.status = EventRegistrationStatus.REGISTERED
            existing.registered_at = now
            existing.source = source or existing.source
            registration = existing
            already = False
        else:
            registration = EventRegistration(
                user_id=user.id,
                event_id=event.id,
                status=EventRegistrationStatus.REGISTERED,
                registered_at=now,
                source=source,
            )
            self.db.add(registration)
            try:
                self.db.flush()
            except IntegrityError as exc:
                self.db.rollback()
                registration = self._registration_for(user, event.id)
                if not registration:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Could not complete registration",
                    ) from exc
                already = registration.status == EventRegistrationStatus.REGISTERED

        self.db.commit()
        self.db.refresh(registration)

        if not already and self.email_service:
            self.email_service.send_event_registration_email(
                email=user.email,
                full_name=user.full_name,
                event_title=event.title,
                event_slug=event.slug,
                starts_at=event.starts_at,
                timezone_name=event.timezone,
            )

        return RegisterResponse(
            registration_id=registration.id,
            event_slug=event.slug,
            already_registered=already,
            status=registration.status.value,
        )

    def cancel_registration(self, user: User, slug: str) -> None:
        event = self._published_event(slug)
        registration = self._active_registration(user, event.id)
        if not registration:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found")
        lifecycle = self.compute_lifecycle(event)
        if lifecycle in {"live", "completed"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You can no longer cancel this registration",
            )
        registration.status = EventRegistrationStatus.CANCELLED
        self.db.commit()

    def join(self, user: User, slug: str) -> JoinResponse:
        event = self._published_event(slug)
        now = self._utcnow()
        registration = self._active_registration(user, event.id)
        if not registration:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Register for this event to join",
            )
        if not self._can_join(event, user, now):
            lifecycle = self.compute_lifecycle(event, now)
            if lifecycle == "cancelled":
                detail = "This event has been cancelled"
            elif lifecycle == "completed":
                detail = "This event has already ended"
            elif not event.youtube_live_url:
                detail = "The live link is not available yet. Check back at start time."
            else:
                detail = "Joining opens 15 minutes before the event starts"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        if registration.join_clicked_at is None:
            registration.join_clicked_at = now
        if registration.checked_in_at is None:
            registration.checked_in_at = now
        self.db.commit()
        self.db.refresh(registration)
        assert event.youtube_live_url is not None
        return JoinResponse(
            youtube_live_url=event.youtube_live_url,
            join_clicked_at=registration.join_clicked_at or now,
        )

    def check_in(self, user: User, slug: str) -> CheckInResponse:
        event = self._published_event(slug)
        now = self._utcnow()
        registration = self._active_registration(user, event.id)
        if not registration:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Register for this event to check in",
            )
        lifecycle = self.compute_lifecycle(event, now)
        if lifecycle in {"cancelled", "completed", "draft", "coming_soon"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Check-in is not available for this event",
            )
        starts_at = self._utc(event.starts_at)
        if starts_at is None or now < starts_at - JOIN_WINDOW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Check-in opens 15 minutes before the event starts",
            )
        if registration.checked_in_at is None:
            registration.checked_in_at = now
            self.db.commit()
            self.db.refresh(registration)
        assert registration.checked_in_at is not None
        return CheckInResponse(checked_in_at=registration.checked_in_at)

    def list_mine(self, user: User) -> list[EventRegistrationPublic]:
        now = self._utcnow()
        rows = self.db.scalars(
            select(EventRegistration)
            .options(selectinload(EventRegistration.event))
            .join(Event)
            .where(
                EventRegistration.user_id == user.id,
                EventRegistration.status == EventRegistrationStatus.REGISTERED,
            )
            .order_by(Event.starts_at.desc())
        ).all()
        result: list[EventRegistrationPublic] = []
        for row in rows:
            result.append(
                EventRegistrationPublic(
                    id=row.id,
                    status=row.status.value,
                    registered_at=row.registered_at,
                    join_clicked_at=row.join_clicked_at,
                    checked_in_at=row.checked_in_at,
                    event=self._card(row.event, user, now),
                )
            )
        return result

    def list_admin(self) -> list[EventAdmin]:
        events = self.db.scalars(select(Event).order_by(Event.starts_at.desc())).all()
        return [self._admin(event) for event in events]

    def get_admin(self, event_id: UUID) -> EventAdmin:
        return self._admin(self._get_by_id(event_id))

    def _assert_slug_free(self, slug: str, *, exclude_id: UUID | None = None) -> None:
        query = select(Event).where(Event.slug == slug)
        if exclude_id:
            query = query.where(Event.id != exclude_id)
        if self.db.scalar(query):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="That event slug is already in use")

    def _validate_times(
        self,
        starts_at: datetime | None,
        ends_at: datetime | None,
        timezone_name: str,
    ) -> None:
        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unknown timezone",
            ) from exc
        if starts_at is None and ends_at is None:
            return
        if starts_at is None or ends_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Set both start and end times, or leave both empty for Coming soon.",
            )
        start = self._aware(starts_at, timezone_name)
        end = self._aware(ends_at, timezone_name)
        if end <= start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event end time must be after the start time",
            )

    def create(self, payload: EventCreate, host: User | None = None) -> EventAdmin:
        self._assert_slug_free(payload.slug)
        self._validate_times(payload.starts_at, payload.ends_at, payload.timezone)
        if payload.price > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Paid events are not available yet. Keep the price at 0.",
            )
        event = Event(
            slug=payload.slug,
            title=payload.title,
            event_type=payload.event_type,
            short_description=payload.short_description,
            description=payload.description,
            cover_image=payload.cover_image,
            starts_at=self._aware(payload.starts_at, payload.timezone) if payload.starts_at else None,
            ends_at=self._aware(payload.ends_at, payload.timezone) if payload.ends_at else None,
            timezone=payload.timezone,
            price=payload.price,
            currency=payload.currency.upper(),
            registration_deadline=(
                self._aware(payload.registration_deadline, payload.timezone)
                if payload.registration_deadline
                else None
            ),
            capacity=payload.capacity,
            host_user_id=host.id if host else None,
            host_name=payload.host_name or (host.full_name if host else None),
            platform=(
                payload.platform.value
                if isinstance(payload.platform, EventPlatform)
                else str(payload.platform)
            ),
            platform_label=payload.platform_label,
            youtube_live_url=payload.youtube_live_url,
            recording_url=payload.recording_url,
            learn_topics=payload.learn_topics,
            audience=payload.audience,
            prerequisites=payload.prerequisites,
            related_course_slug=payload.related_course_slug
            or self._related_slug_from_keep_learning(
                [offer.model_dump() if hasattr(offer, "model_dump") else offer for offer in payload.keep_learning]
            ),
            keep_learning=normalize_keep_learning(
                [offer.model_dump() if hasattr(offer, "model_dump") else offer for offer in payload.keep_learning]
            ),
            seo_title=payload.seo_title,
            seo_description=payload.seo_description,
            published=payload.published,
            cancelled=payload.cancelled,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return self._admin(event)

    def update(self, event_id: UUID, payload: EventUpdate) -> EventAdmin:
        event = self._get_by_id(event_id)
        data = payload.model_dump(exclude_unset=True)
        timezone_name = data.get("timezone", event.timezone)
        starts_at = data["starts_at"] if "starts_at" in data else event.starts_at
        ends_at = data["ends_at"] if "ends_at" in data else event.ends_at
        self._validate_times(starts_at, ends_at, timezone_name)
        if "slug" in data and data["slug"] != event.slug:
            self._assert_slug_free(data["slug"], exclude_id=event.id)
        if data.get("price", event.price) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Paid events are not available yet. Keep the price at 0.",
            )
        if "starts_at" in data:
            data["starts_at"] = (
                self._aware(data["starts_at"], timezone_name) if data["starts_at"] else None
            )
        if "ends_at" in data:
            data["ends_at"] = self._aware(data["ends_at"], timezone_name) if data["ends_at"] else None
        if "registration_deadline" in data and data["registration_deadline"] is not None:
            data["registration_deadline"] = self._aware(data["registration_deadline"], timezone_name)
        if "currency" in data and data["currency"]:
            data["currency"] = data["currency"].upper()
        if "platform" in data and data["platform"] is not None:
            platform = data["platform"]
            data["platform"] = platform.value if isinstance(platform, EventPlatform) else str(platform)
        if "keep_learning" in data:
            offers = normalize_keep_learning(data["keep_learning"])
            data["keep_learning"] = offers
            if "related_course_slug" not in data:
                data["related_course_slug"] = self._related_slug_from_keep_learning(offers)
        for key, value in data.items():
            setattr(event, key, value)
        self.db.commit()
        self.db.refresh(event)
        return self._admin(event)
