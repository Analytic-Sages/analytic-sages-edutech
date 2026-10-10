"""Close RealtimeKit when a class is over.

The LMS clock only stops new join tokens. RealtimeKit keeps the room and the
recorder until this service kick-alls the active session and stops any recording
that is still capturing. A later sweep does not touch an already closed meeting,
and it never writes a recording id into ``realtimekit_meeting_id`` or edits attendance.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.roles import UserRole
from app.models.classroom import LiveSession, LiveSessionStatus
from app.models.user import User
from app.services.realtimekit import RealtimeKitError, RealtimeKitService

logger = logging.getLogger(__name__)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def session_should_end(session: LiveSession, now: datetime) -> bool:
    """True when this row's RealtimeKit room should be closed now."""
    meeting_id = (session.realtimekit_meeting_id or "").strip()
    if not meeting_id or session.realtimekit_closed_at is not None:
        return False
    if session.status in {LiveSessionStatus.ENDED, LiveSessionStatus.CANCELLED}:
        return True
    return _aware(now) >= _aware(session.ends_at)


class MeetingCloseService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        realtimekit: RealtimeKitService | None = None,
    ) -> None:
        self.db = db
        self.settings = settings
        self.realtimekit = realtimekit or RealtimeKitService(settings)

    def _authorized_staff_present(self, session: LiveSession) -> bool | None:
        """Whether an authorized staff member is currently in this live room.

        Returns None when RealtimeKit presence cannot be verified. In that case,
        the close sweep fails open so a transient provider/API failure cannot cut
        off a class that may still have an instructor present.
        """
        meeting_id = str(session.realtimekit_meeting_id or "").strip()
        try:
            provider_session = self.realtimekit.find_session_for_meeting(meeting_id)
            if not provider_session:
                return False

            provider_status = str(provider_session.get("status") or "").upper()
            if provider_status == "ENDED":
                return False
            if provider_status != "LIVE":
                logger.warning(
                    "Cannot verify active RealtimeKit session %s for LMS session %s "
                    "(provider status=%r); leaving room open",
                    meeting_id,
                    session.id,
                    provider_status or None,
                )
                return None

            provider_session_id = str(provider_session.get("id") or "").strip()
            if not provider_session_id:
                logger.warning(
                    "RealtimeKit returned a live session without an id for LMS session %s; "
                    "leaving room open",
                    session.id,
                )
                return None

            participants = self.realtimekit.list_all_session_participants(
                provider_session_id, include_peer_events=False
            )
        except RealtimeKitError:
            logger.exception(
                "Could not verify staff presence for RealtimeKit meeting %s; leaving it open",
                meeting_id,
            )
            return None

        staff_ids: set[UUID] = set()
        for participant in participants:
            # Session participant history includes people who have already left.
            # Only count participants whose current session interval is still open.
            if participant.get("left_at"):
                continue
            raw_id = participant.get("custom_participant_id") or participant.get(
                "customParticipantId"
            )
            if not raw_id:
                continue
            try:
                staff_ids.add(UUID(str(raw_id)))
            except (ValueError, TypeError, AttributeError):
                continue

        if not staff_ids:
            return False

        return (
            self.db.scalar(
                select(User.id).where(
                    User.id.in_(staff_ids),
                    User.is_active.is_(True),
                    User.role.in_(
                        {UserRole.ADMIN, UserRole.INSTRUCTOR, UserRole.OPERATIONS}
                    ),
                )
            )
            is not None
        )

    def close_elapsed(self) -> dict[str, int]:
        """Close due meetings unless an authorized staff member is still present."""
        now = datetime.now(timezone.utc)
        sessions = list(
            self.db.scalars(
                select(LiveSession).where(
                    LiveSession.realtimekit_closed_at.is_(None),
                    LiveSession.realtimekit_meeting_id.is_not(None),
                )
            ).all()
        )
        closed = failed = skipped = 0
        warned_unconfigured = False
        for session in sessions:
            if not session_should_end(session, now):
                skipped += 1
                continue

            # An explicit end/cancel action always wins. For a session that only
            # reached its scheduled end, keep it alive while authorized staff remain.
            if session.status not in {LiveSessionStatus.ENDED, LiveSessionStatus.CANCELLED}:
                staff_present = self._authorized_staff_present(session)
                if staff_present is None:
                    failed += 1
                    continue
                if staff_present:
                    skipped += 1
                    logger.info(
                        "Keeping classroom session %s open past scheduled end: "
                        "authorized staff still present",
                        session.id,
                    )
                    continue

            meeting_id = str(session.realtimekit_meeting_id)
            if (
                not meeting_id.startswith("mock-")
                and not self.realtimekit.configured
            ):
                if not warned_unconfigured:
                    logger.warning(
                        "RealtimeKit is not configured; elapsed meetings were left running"
                    )
                    warned_unconfigured = True
                failed += 1
                continue
            outcome = self._close_one(session)
            if outcome is None:
                skipped += 1
            elif outcome:
                closed += 1
            else:
                failed += 1
        return {"closed": closed, "failed": failed, "skipped": skipped}

    def close_session(self, session: LiveSession) -> bool:
        """Close one session when it is due. Returns True when it is finished."""
        self.db.refresh(session)
        if not session_should_end(session, datetime.now(timezone.utc)):
            return session.realtimekit_closed_at is not None
        meeting_id = str(session.realtimekit_meeting_id or "")
        if not meeting_id.startswith("mock-") and not self.realtimekit.configured:
            return False
        outcome = self._close_one(session)
        return bool(outcome)

    def _close_one(self, session: LiveSession) -> bool | None:
        """True when closed, False when the provider call failed, None if no longer due."""
        self.db.refresh(session)
        now = datetime.now(timezone.utc)
        if session.realtimekit_closed_at is not None:
            return None
        if not session_should_end(session, now):
            return None
        meeting_id = str(session.realtimekit_meeting_id)
        if not self.realtimekit.end_live_meeting(meeting_id):
            logger.warning(
                "RealtimeKit meeting %s for session %s is still open; will retry",
                meeting_id,
                session.id,
            )
            return False
        self.db.execute(
            update(LiveSession)
            .where(
                LiveSession.id == session.id,
                LiveSession.realtimekit_closed_at.is_(None),
            )
            .values(realtimekit_closed_at=now)
        )
        self.db.commit()
        if session.status == LiveSessionStatus.CANCELLED:
            reason = "session_cancelled"
        elif session.status == LiveSessionStatus.ENDED:
            reason = "explicit_session_end"
        else:
            reason = "scheduled_end_without_authorized_staff"

        logger.info(
            "Ended live room and recording for session %s meeting %s (reason=%s)",
            session.id,
            meeting_id,
            reason,
        )
        return True
