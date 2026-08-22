from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import Settings
from app.core.roles import UserRole
from app.models.classroom import (
    Cohort,
    CohortMember,
    CohortMemberRole,
    CohortStatus,
    LiveSession,
    LiveSessionStatus,
)
from app.models.user import User
from app.schemas.classroom import (
    ClassroomJoinResponse,
    LiveSessionPublic,
    PublicCohortCard,
    SessionResource,
)
from app.services.instructors import InstructorService
from app.services.realtimekit import RealtimeKitError, RealtimeKitService

logger = logging.getLogger(__name__)

# Allow students into the room this many minutes before starts_at.
EARLY_JOIN_MINUTES = 15


class ClassroomService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.realtimekit = RealtimeKitService(settings)

    def _utcnow(self) -> datetime:
        return datetime.now(timezone.utc)

    def _member_for(self, user: User, cohort_id: UUID) -> CohortMember | None:
        return self.db.scalar(
            select(CohortMember).where(
                CohortMember.cohort_id == cohort_id,
                CohortMember.user_id == user.id,
            )
        )

    def _is_staff(self, user: User) -> bool:
        return user.role in {UserRole.ADMIN, UserRole.INSTRUCTOR}

    def _can_access(self, user: User, session: LiveSession) -> CohortMember | None:
        member = self._member_for(user, session.cohort_id)
        if member:
            return member
        if self._is_staff(user):
            # Staff can observe any session; treat as instructor for presets.
            return None
        return None

    def _effective_phase(self, session: LiveSession) -> str:
        if session.status == LiveSessionStatus.CANCELLED:
            return "cancelled"
        if session.status == LiveSessionStatus.ENDED:
            return "ended"
        if session.status == LiveSessionStatus.LIVE:
            return "live"

        now = self._utcnow()
        starts = session.starts_at
        ends = session.ends_at
        if starts.tzinfo is None:
            starts = starts.replace(tzinfo=timezone.utc)
        if ends.tzinfo is None:
            ends = ends.replace(tzinfo=timezone.utc)

        if now > ends:
            return "ended"
        if now >= starts - timedelta(minutes=EARLY_JOIN_MINUTES):
            return "live"
        return "upcoming"

    def _can_join(self, phase: str) -> bool:
        return phase == "live"

    def list_public_cohorts(self) -> list[PublicCohortCard]:
        """Open/active cohorts for marketing (Instructor-Led). No auth required."""
        cohorts = list(
            self.db.scalars(
                select(Cohort)
                .where(Cohort.status.in_([CohortStatus.OPEN, CohortStatus.ACTIVE]))
                .options(joinedload(Cohort.course), joinedload(Cohort.sessions))
                .order_by(Cohort.starts_at.asc().nulls_last())
            )
            .unique()
            .all()
        )
        cards: list[PublicCohortCard] = []
        instructors = InstructorService(self.db)
        for cohort in cohorts:
            sessions = sorted(
                [s for s in (cohort.sessions or []) if s.status != LiveSessionStatus.CANCELLED],
                key=lambda s: s.starts_at,
            )
            next_session = None
            for sess in sessions:
                phase = self._effective_phase(sess)
                if phase in {"live", "upcoming"}:
                    next_session = sess
                    break
            cards.append(
                PublicCohortCard(
                    id=cohort.id,
                    name=cohort.name,
                    slug=cohort.slug,
                    description=cohort.description or "",
                    status=cohort.status.value,  # type: ignore[arg-type]
                    registration_deadline=cohort.registration_deadline,
                    starts_at=cohort.starts_at,
                    ends_at=cohort.ends_at,
                    price=cohort.price,
                    currency=cohort.currency,
                    course_title=cohort.course.title if cohort.course else None,
                    course_slug=cohort.course.slug if cohort.course else None,
                    next_session_title=next_session.title if next_session else None,
                    next_session_starts_at=next_session.starts_at if next_session else None,
                    next_session_phase=(
                        self._effective_phase(next_session) if next_session else None  # type: ignore[arg-type]
                    ),
                    sessions_count=len(sessions),
                    instructors=instructors.list_for_cohort(cohort),
                )
            )
        return cards

    def _preset_for(self, member: CohortMember | None, user: User) -> str:
        if member and member.role in {CohortMemberRole.INSTRUCTOR, CohortMemberRole.TA}:
            return self.settings.realtimekit_host_preset
        if self._is_staff(user):
            return self.settings.realtimekit_host_preset
        return self.settings.realtimekit_participant_preset

    def _to_public(
        self, session: LiveSession, *, member: CohortMember | None, staff: bool
    ) -> LiveSessionPublic:
        phase = self._effective_phase(session)
        resources: list[SessionResource] = []
        for item in session.resources or []:
            if isinstance(item, dict) and item.get("title") and item.get("url"):
                resources.append(SessionResource.model_validate(item))

        objectives = [
            str(o) for o in (session.objectives or []) if o is not None and str(o).strip()
        ]

        course_title = None
        if session.cohort and session.cohort.course:
            course_title = session.cohort.course.title

        role = None
        if member:
            role = member.role.value
        elif staff:
            role = "instructor"

        return LiveSessionPublic(
            id=session.id,
            cohort_id=session.cohort_id,
            cohort_name=session.cohort.name if session.cohort else "",
            cohort_slug=session.cohort.slug if session.cohort else "",
            course_title=course_title,
            title=session.title,
            week_label=session.week_label,
            session_number=session.session_number,
            objectives=objectives,
            resources=resources,
            assignment_summary=session.assignment_summary,
            starts_at=session.starts_at,
            ends_at=session.ends_at,
            status=session.status.value,
            phase=phase,  # type: ignore[arg-type]
            recording_url=session.recording_url,
            can_join=self._can_join(phase) and (member is not None or staff),
            member_role=role,  # type: ignore[arg-type]
        )

    def list_my_sessions(self, user: User) -> list[LiveSessionPublic]:
        if self._is_staff(user):
            sessions = list(
                self.db.scalars(
                    select(LiveSession)
                    .options(joinedload(LiveSession.cohort).joinedload(Cohort.course))
                    .order_by(LiveSession.starts_at.asc())
                )
                .unique()
                .all()
            )
            return [self._to_public(s, member=None, staff=True) for s in sessions]

        memberships = list(
            self.db.scalars(select(CohortMember).where(CohortMember.user_id == user.id)).all()
        )
        if not memberships:
            return []

        cohort_ids = [m.cohort_id for m in memberships]
        member_by_cohort = {m.cohort_id: m for m in memberships}

        sessions = list(
            self.db.scalars(
                select(LiveSession)
                .where(LiveSession.cohort_id.in_(cohort_ids))
                .options(joinedload(LiveSession.cohort).joinedload(Cohort.course))
                .order_by(LiveSession.starts_at.asc())
            )
            .unique()
            .all()
        )
        return [
            self._to_public(s, member=member_by_cohort.get(s.cohort_id), staff=False)
            for s in sessions
        ]

    def get_session_for_user(self, user: User, session_id: UUID) -> LiveSessionPublic:
        session = self.db.scalar(
            select(LiveSession)
            .where(LiveSession.id == session_id)
            .options(joinedload(LiveSession.cohort).joinedload(Cohort.course))
        )
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        member = self._can_access(user, session)
        staff = self._is_staff(user)
        if member is None and not staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this cohort",
            )
        return self._to_public(session, member=member, staff=staff)

    def join_session(self, user: User, session_id: UUID) -> ClassroomJoinResponse:
        session = self.db.scalar(
            select(LiveSession)
            .where(LiveSession.id == session_id)
            .options(joinedload(LiveSession.cohort))
        )
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        member = self._can_access(user, session)
        staff = self._is_staff(user)
        if member is None and not staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this cohort",
            )

        phase = self._effective_phase(session)
        preset = self._preset_for(member, user)
        display_name = user.full_name or user.email.split("@")[0]

        if phase != "live":
            return ClassroomJoinResponse(
                session_id=session.id,
                mode=self.realtimekit.mode,  # type: ignore[arg-type]
                auth_token=None,
                meeting_id=session.realtimekit_meeting_id,
                preset=preset,
                display_name=display_name,
                phase=phase,  # type: ignore[arg-type]
                message=(
                    "This class has not started yet."
                    if phase == "upcoming"
                    else "This class has ended."
                    if phase == "ended"
                    else "This class was cancelled."
                ),
            )

        try:
            meeting_id = session.realtimekit_meeting_id
            if meeting_id and str(meeting_id).startswith("mock-"):
                meeting_id = None
            if not meeting_id:
                meeting_id = self.realtimekit.create_meeting(title=session.title)
                session.realtimekit_meeting_id = meeting_id
                self.db.commit()

            try:
                participant = self.realtimekit.add_participant(
                    meeting_id=meeting_id,
                    custom_participant_id=str(user.id),
                    name=display_name,
                    preset_name=preset,
                )
            except RealtimeKitError as add_exc:
                # Stale meeting after App ID / token rotation → recreate once.
                if add_exc.status_code == 404:
                    logger.warning(
                        "RealtimeKit meeting %s missing (404); recreating for session %s",
                        meeting_id,
                        session.id,
                    )
                    meeting_id = self.realtimekit.create_meeting(title=session.title)
                    session.realtimekit_meeting_id = meeting_id
                    self.db.commit()
                    participant = self.realtimekit.add_participant(
                        meeting_id=meeting_id,
                        custom_participant_id=str(user.id),
                        name=display_name,
                        preset_name=preset,
                    )
                else:
                    raise
        except RealtimeKitError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

        return ClassroomJoinResponse(
            session_id=session.id,
            mode=self.realtimekit.mode,  # type: ignore[arg-type]
            auth_token=participant.get("token"),
            meeting_id=meeting_id,
            preset=preset,
            display_name=display_name,
            phase="live",
            message=None if self.realtimekit.configured else "RealtimeKit mock mode (no Cloudflare keys).",
        )
