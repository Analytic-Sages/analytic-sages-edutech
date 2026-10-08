"""Close RealtimeKit when a class is over.

The LMS clock only stops new join tokens. RealtimeKit keeps the room and the
recorder until this service kick-alls the active session and stops any recording
that is still capturing. A later sweep does not touch an already closed meeting,
and it never writes a recording id into ``realtimekit_meeting_id`` or edits attendance.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.classroom import LiveSession, LiveSessionStatus
from app.services.realtimekit import RealtimeKitService

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

    def close_elapsed(self) -> dict[str, int]:
        """Close every due meeting. Safe to run repeatedly."""
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
        logger.info(
            "Ended live room and recording for session %s meeting %s",
            session.id,
            meeting_id,
        )
        return True
