from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.billing import ObligationStatus
from app.core.config import Settings
from app.core.roles import UserRole
from app.models.billing import StudentBillingAccount
from app.models.classroom import (
    Cohort,
    CohortMember,
    CohortMemberRole,
    CohortStatus,
    LiveSession,
    LiveSessionStatus,
    RecordingStatus,
    SessionRecording,
)
from app.models.user import User
from app.schemas.classroom import (
    ClassroomJoinResponse,
    LiveSessionPublic,
    PublicCohortCard,
    SessionResource,
)
from app.services.calendar_ics import CalendarEvent, build_calendar
from app.services.instructors import InstructorService
from app.services.realtimekit import RealtimeKitError, RealtimeKitService
from app.services.waitlist import WaitlistService

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

    def _is_admin(self, user: User) -> bool:
        return user.role == UserRole.ADMIN

    def _can_access(self, user: User, session: LiveSession) -> CohortMember | None:
        member = self._member_for(user, session.cohort_id)
        if member:
            return member
        if self._is_admin(user):
            # Admins can observe any session; treat as instructor for presets.
            return None
        return None

    def _payment_standing_block(self, user: User, session: LiveSession) -> str | None:
        """Block reason when a paying student owes tuition for this session's cohort.

        Only students are evaluated. A manual ``access_blocked`` flag or a past-due
        open obligation removes live-session access until the account is settled.
        """
        if user.role != UserRole.STUDENT:
            return None

        cohort = session.cohort
        accounts = list(
            self.db.scalars(
                select(StudentBillingAccount)
                .options(selectinload(StudentBillingAccount.obligations))
                .where(StudentBillingAccount.student_id == user.id)
            ).all()
        )
        relevant = [
            a
            for a in accounts
            if a.cohort_id == session.cohort_id
            or (cohort is not None and cohort.course_id is not None and a.course_id == cohort.course_id)
        ]
        now = self._utcnow()
        for account in relevant:
            if account.access_blocked:
                return "Your live session access is restricted until your tuition is paid."
            for obligation in account.obligations:
                if obligation.status in {
                    ObligationStatus.OPEN,
                    ObligationStatus.PROCESSING,
                    ObligationStatus.UPCOMING,
                    ObligationStatus.PAST_DUE,
                }:
                    due = obligation.due_date
                    if due is not None:
                        if due.tzinfo is None:
                            due = due.replace(tzinfo=timezone.utc)
                        if obligation.status == ObligationStatus.PAST_DUE or due < now:
                            return (
                                "A tuition installment is past due. Pay the outstanding "
                                "amount to regain access to live sessions."
                            )
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
                    waitlist_open=WaitlistService(self.db).is_waitlist_open(cohort),
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
        self,
        session: LiveSession,
        *,
        member: CohortMember | None,
        staff: bool,
        user: User,
        recordings: dict[UUID, SessionRecording] | None = None,
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

        blocked_reason = None
        if member is not None and member.role == CohortMemberRole.STUDENT:
            blocked_reason = self._payment_standing_block(user, session)

        # A ready Cloudflare Stream copy wins over any leftover temporary URL so
        # students hit the enrollment-gated playback endpoint after that link expires.
        recording = (recordings or {}).get(session.id) if recordings is not None else self._recording_for(session.id)
        stream_ready = recording is not None and recording.status == RecordingStatus.READY
        r2_ready = (
            recording is not None
            and recording.storage_provider == "r2"
            and bool(recording.storage_key)
        )
        if stream_ready or r2_ready:
            recording_status = "ready"
            recording_watch_url = (
                f"/api/v1/cohorts/{session.cohort_id}/sessions/{session.id}/recording"
            )
            public_recording_url = None
        elif session.recording_url:
            recording_status = "ready"
            recording_watch_url = session.recording_url
            public_recording_url = session.recording_url
        elif recording is not None:
            recording_status = recording.status.value
            recording_watch_url = None
            public_recording_url = None
        else:
            recording_status = "none"
            recording_watch_url = None
            public_recording_url = None

        return LiveSessionPublic(
            id=session.id,
            cohort_id=session.cohort_id,
            cohort_name=session.cohort.name if session.cohort else "",
            cohort_slug=session.cohort.slug if session.cohort else "",
            course_title=course_title,
            title=session.title,
            week_label=session.week_label,
            session_number=session.session_number,
            session_type=session.session_type.value,  # type: ignore[arg-type]
            objectives=objectives,
            resources=resources,
            assignment_summary=session.assignment_summary,
            description=session.description,
            timezone=session.timezone or "UTC",
            meeting_url=session.meeting_url,
            instructor_name=(
                session.instructor_user.full_name if session.instructor_user else None
            ),
            starts_at=session.starts_at,
            ends_at=session.ends_at,
            status=session.status.value,
            phase=phase,  # type: ignore[arg-type]
            recording_url=public_recording_url,
            recording_status=recording_status,  # type: ignore[arg-type]
            recording_watch_url=recording_watch_url,
            can_join=self._can_join(phase) and (member is not None or staff) and blocked_reason is None,
            member_role=role,  # type: ignore[arg-type]
            access_blocked=blocked_reason is not None,
            access_blocked_reason=blocked_reason,
        )

    def _recording_for(self, session_id: UUID) -> SessionRecording | None:
        return self.db.scalar(
            select(SessionRecording).where(SessionRecording.session_id == session_id)
        )

    def _recordings_for(self, session_ids: list[UUID]) -> dict[UUID, SessionRecording]:
        """Batch-load recordings for a set of sessions (avoids N+1 in lists)."""
        if not session_ids:
            return {}
        rows = list(
            self.db.scalars(
                select(SessionRecording).where(SessionRecording.session_id.in_(session_ids))
            ).all()
        )
        return {row.session_id: row for row in rows}

    def list_my_sessions(self, user: User) -> list[LiveSessionPublic]:
        if self._is_admin(user):
            sessions = list(
                self.db.scalars(
                    select(LiveSession)
                    .options(
                        joinedload(LiveSession.cohort).joinedload(Cohort.course),
                        joinedload(LiveSession.instructor_user),
                    )
                    .order_by(LiveSession.starts_at.asc())
                )
                .unique()
                .all()
            )
            recordings = self._recordings_for([s.id for s in sessions])
            return [
                self._to_public(s, member=None, staff=True, user=user, recordings=recordings)
                for s in sessions
            ]

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
                .options(
                    joinedload(LiveSession.cohort).joinedload(Cohort.course),
                    joinedload(LiveSession.instructor_user),
                )
                .order_by(LiveSession.starts_at.asc())
            )
            .unique()
            .all()
        )
        recordings = self._recordings_for([s.id for s in sessions])
        return [
            self._to_public(
                s,
                member=member_by_cohort.get(s.cohort_id),
                staff=False,
                user=user,
                recordings=recordings,
            )
            for s in sessions
        ]

    def calendar_ics(self, user: User) -> str:
        """RFC 5545 feed of every session the user can see.

        Reuses ``list_my_sessions`` so authorization matches the classroom exactly:
        students get their cohorts, instructors/admins get everything. Each event
        carries a pop-up reminder and links back to the session page.
        """
        base = self.settings.frontend_url.rstrip("/")
        events: list[CalendarEvent] = []
        for session in self.list_my_sessions(user):
            if session.session_type == "office_hour":
                context = f"{session.cohort_name} · {session.week_label} · Office Hour"
            else:
                context = (
                    f"{session.cohort_name} · {session.week_label} · "
                    f"Session {session.session_number}"
                )
            description_parts = [context]
            if session.objectives:
                description_parts.append("")
                description_parts.extend(f"- {objective}" for objective in session.objectives)
            if session.assignment_summary:
                description_parts.extend(["", f"Assignment: {session.assignment_summary}"])
            events.append(
                CalendarEvent(
                    uid=f"session-{session.id}@analyticsages.io",
                    starts_at=session.starts_at,
                    ends_at=session.ends_at,
                    summary=session.title,
                    description="\n".join(description_parts),
                    location=f"{base}/classroom/{session.id}",
                )
            )
        return build_calendar(events, calendar_name="Analytic Sages Classroom")

    def get_session_for_user(self, user: User, session_id: UUID) -> LiveSessionPublic:
        session = self.db.scalar(
            select(LiveSession)
            .where(LiveSession.id == session_id)
            .options(
                joinedload(LiveSession.cohort).joinedload(Cohort.course),
                joinedload(LiveSession.instructor_user),
            )
        )
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        member = self._can_access(user, session)
        staff = self._is_admin(user)
        if member is None and not staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this cohort",
            )
        return self._to_public(session, member=member, staff=staff, user=user)

    def join_session(self, user: User, session_id: UUID) -> ClassroomJoinResponse:
        session = self.db.scalar(
            select(LiveSession)
            .where(LiveSession.id == session_id)
            .options(joinedload(LiveSession.cohort))
        )
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        member = self._can_access(user, session)
        staff = self._is_admin(user)
        if member is None and not staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this cohort",
            )

        blocked_reason = self._payment_standing_block(user, session)
        if blocked_reason:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=blocked_reason)

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
