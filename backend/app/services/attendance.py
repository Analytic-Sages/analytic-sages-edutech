"""Reconcile Cloudflare RealtimeKit participant data into LMS attendance.

Runs *post-session* (idempotently) and is deliberately independent of the
recording sync: attendance must succeed even if the recording hand-off fails,
and vice-versa. The provider is the source of truth for presence; the LMS owns
the final attendance record and any manual override.

Identity mapping uses the authenticated ``custom_participant_id`` we set on join
(the LMS user UUID), never a display name — an unmatched participant is flagged
for instructor review instead of being guessed.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.core.live import AttendanceStatus, AttendanceSyncStatus
from app.models.attendance import Attendance, AttendanceInterval, AttendanceParticipant
from app.models.classroom import (
    Cohort,
    CohortMember,
    CohortMemberRole,
    LiveSession,
    LiveSessionStatus,
)
from app.models.user import User
from app.schemas.attendance import (
    AttendanceIntervalPublic,
    AttendanceParticipantPublic,
    AttendanceSyncResult,
    ExpectedStudentRow,
    SessionAttendanceDetail,
    SessionAttendanceSyncRow,
)
from app.services.realtimekit import RealtimeKitError, RealtimeKitService

logger = logging.getLogger(__name__)

PROVIDER = "realtimekit"

# provider Event names inside a participant's peer_events list
_PEER_JOIN_EVENTS = {"PEER_JOINING", "PEER_JOINED", "PEER_CREATED"}
_PEER_LEAVE_EVENTS = {"PEER_LEAVING", "PEER_LEFT"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _parse_dt(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return _ensure_utc(value)
    text = str(value).strip().strip('"')
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return _ensure_utc(datetime.fromisoformat(text))
    except ValueError:
        return None


def _delta_seconds(start: datetime | None, end: datetime | None) -> int:
    if not start or not end or end <= start:
        return 0
    return int((end - start).total_seconds())


def _duration_to_seconds(raw: dict) -> int:
    """RealtimeKit reports ``duration`` in minutes (float) → convert to seconds."""
    value = raw.get("duration")
    if value is None:
        return 0
    try:
        return max(int(round(float(value) * 60)), 0)
    except (TypeError, ValueError):
        return 0


def _display_name(raw: dict) -> str | None:
    for key in ("display_name", "displayName", "name"):
        value = raw.get(key)
        if value:
            return str(value)
    profile = raw.get("profile")
    if isinstance(profile, dict) and profile.get("name"):
        return str(profile["name"])
    return None


class AttendanceSyncService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        realtimekit: RealtimeKitService | None = None,
    ) -> None:
        self.db = db
        self.settings = settings
        self.realtimekit = realtimekit or RealtimeKitService(settings)

    # ---------- rules ----------

    def _rules(self, session: LiveSession) -> tuple[int, float, int]:
        """(min_seconds, min_percent, late_grace_minutes) for the session's cohort."""
        cohort = self.db.get(Cohort, session.cohort_id)
        config: dict = {}
        if cohort and isinstance(cohort.enrollment_settings, dict):
            config = cohort.enrollment_settings.get("attendance") or {}
        min_seconds = int(config.get("min_seconds", self.settings.attendance_default_min_seconds))
        min_percent = float(config.get("min_percent", self.settings.attendance_default_min_percent))
        late_grace = int(
            config.get("late_grace_minutes", self.settings.attendance_late_grace_minutes)
        )
        return max(min_seconds, 0), max(min_percent, 0.0), max(late_grace, 0)

    def _required_seconds(self, session: LiveSession, min_seconds: int, min_percent: float) -> int:
        scheduled = _delta_seconds(session.starts_at, session.ends_at)
        required = min_seconds
        if scheduled > 0 and min_percent > 0:
            required = max(required, int(scheduled * min_percent / 100.0))
        return required

    def _status_for(
        self,
        session: LiveSession,
        total_seconds: int,
        first_joined_at: datetime | None,
        min_seconds: int,
        min_percent: float,
        late_grace: int,
    ) -> AttendanceStatus:
        if total_seconds <= 0:
            return AttendanceStatus.ABSENT
        if total_seconds < self._required_seconds(session, min_seconds, min_percent):
            # Some attendance, but below the required threshold.
            return AttendanceStatus.LATE
        if first_joined_at and session.starts_at:
            if first_joined_at > _ensure_utc(session.starts_at) + timedelta(minutes=late_grace):
                return AttendanceStatus.LATE
        return AttendanceStatus.ATTENDED

    # ---------- identity matching ----------

    def _match(self, session: LiveSession, custom_participant_id: object) -> tuple[User | None, CohortMember | None]:
        """Map a participant to an enrolled LMS user using the authenticated id."""
        if not custom_participant_id:
            return None, None
        try:
            user_id = UUID(str(custom_participant_id))
        except (ValueError, TypeError, AttributeError):
            return None, None
        user = self.db.get(User, user_id)
        if user is None or not user.is_active:
            return None, None
        member = self.db.scalar(
            select(CohortMember).where(
                CohortMember.cohort_id == session.cohort_id,
                CohortMember.user_id == user_id,
            )
        )
        if member is None:
            return None, None
        return user, member

    # ---------- intervals ----------

    def _build_intervals(
        self, raw: dict
    ) -> list[tuple[datetime | None, datetime | None, str | None]]:
        """Presence windows from the participant's peer events (reconnects)."""
        events = raw.get("peer_events") or raw.get("peerEvents") or []
        intervals: list[tuple[datetime | None, datetime | None, str | None]] = []
        open_start: datetime | None = None
        open_event: str | None = None
        for event in sorted(events, key=lambda e: str(e.get("created_at") or e.get("createdAt") or "")):
            name = str(event.get("event_name") or event.get("eventName") or "").upper()
            when = _parse_dt(event.get("created_at") or event.get("createdAt"))
            event_id = event.get("id")
            if name in _PEER_JOIN_EVENTS:
                if open_start is None:
                    open_start = when
                    open_event = str(event_id) if event_id else None
            elif name in _PEER_LEAVE_EVENTS and open_start is not None:
                intervals.append((open_start, when, open_event))
                open_start = None
                open_event = None
        if open_start is not None:
            intervals.append((open_start, None, open_event))
        return intervals

    def _total_from_intervals(
        self, intervals: list[tuple[datetime | None, datetime | None, str | None]]
    ) -> int:
        """Sum non-overlapping attended time (merges overlapping spans)."""
        spans = sorted(
            (_ensure_utc(j), _ensure_utc(l))
            for j, l, _ in intervals
            if j is not None and l is not None and l > j
        )
        total = 0.0
        current_start: datetime | None = None
        current_end: datetime | None = None
        for start, end in spans:
            if current_end is None or start > current_end:
                if current_start is not None and current_end is not None:
                    total += (current_end - current_start).total_seconds()
                current_start, current_end = start, end
            else:
                current_end = max(current_end, end)
        if current_start is not None and current_end is not None:
            total += (current_end - current_start).total_seconds()
        return int(total)

    def _replace_intervals(
        self,
        record: AttendanceParticipant,
        intervals: list[tuple[datetime | None, datetime | None, str | None]],
    ) -> None:
        """Rebuild a participant's intervals so repeated syncs stay idempotent."""
        self.db.execute(
            delete(AttendanceInterval).where(AttendanceInterval.participant_id == record.id)
        )
        self.db.flush()
        for joined_at, left_at, event_id in intervals:
            self.db.add(
                AttendanceInterval(
                    id=uuid.uuid4(),
                    participant_id=record.id,
                    joined_at=joined_at,
                    left_at=left_at,
                    duration_seconds=_delta_seconds(joined_at, left_at),
                    provider_event_id=event_id,
                    source="peer_events" if event_id else "summary",
                )
            )
        self.db.flush()

    # ---------- authoritative attendance writes ----------

    def _write_attendance(
        self,
        session: LiveSession,
        user: User,
        record: AttendanceParticipant,
        status_value: AttendanceStatus,
    ) -> bool:
        """Upsert the authoritative attendance row from provider data.

        A manual override is never overwritten — only its sync metadata is refreshed.
        """
        existing = self.db.scalar(
            select(Attendance).where(
                Attendance.session_id == session.id, Attendance.user_id == user.id
            )
        )
        now = _utcnow()
        if existing is not None and existing.manual_override:
            existing.last_synced_at = now
            existing.sync_status = AttendanceSyncStatus.OK
            return False
        if existing is None:
            existing = Attendance(
                id=uuid.uuid4(), session_id=session.id, user_id=user.id, status=status_value
            )
            self.db.add(existing)
        existing.status = status_value
        existing.provider = PROVIDER
        existing.provider_meeting_id = session.realtimekit_meeting_id
        existing.provider_session_id = record.provider_session_id
        existing.provider_participant_id = record.provider_participant_id
        existing.first_joined_at = record.first_joined_at
        existing.last_left_at = record.last_left_at
        existing.total_attendance_seconds = record.total_attendance_seconds
        existing.sync_status = AttendanceSyncStatus.OK
        existing.last_synced_at = now
        return True

    def _write_manual_resolution(
        self,
        session: LiveSession,
        user: User,
        record: AttendanceParticipant,
        *,
        status_value: AttendanceStatus,
        actor: User | None,
        reason: str | None,
    ) -> None:
        """Record a human resolution and mark it as a manual override."""
        existing = self.db.scalar(
            select(Attendance).where(
                Attendance.session_id == session.id, Attendance.user_id == user.id
            )
        )
        if existing is None:
            existing = Attendance(
                id=uuid.uuid4(), session_id=session.id, user_id=user.id, status=status_value
            )
            self.db.add(existing)
        existing.status = status_value
        existing.provider = PROVIDER
        existing.provider_session_id = record.provider_session_id
        existing.provider_participant_id = record.provider_participant_id
        existing.first_joined_at = record.first_joined_at
        existing.last_left_at = record.last_left_at
        existing.total_attendance_seconds = record.total_attendance_seconds
        existing.manual_override = True
        existing.override_reason = reason
        existing.overridden_by = actor.id if actor else None
        existing.sync_status = AttendanceSyncStatus.OK
        existing.last_synced_at = _utcnow()

    def _mark_missing_absent(self, session: LiveSession, matched_user_ids: set) -> int:
        """Finalized sessions only: expected students with no presence → Absent."""
        students = list(
            self.db.scalars(
                select(CohortMember).where(
                    CohortMember.cohort_id == session.cohort_id,
                    CohortMember.role == CohortMemberRole.STUDENT,
                )
            ).all()
        )
        if not students:
            return 0
        user_ids = [member.user_id for member in students]
        existing_rows = {
            row.user_id: row
            for row in self.db.scalars(
                select(Attendance).where(
                    Attendance.session_id == session.id, Attendance.user_id.in_(user_ids)
                )
            ).all()
        }
        now = _utcnow()
        written = 0
        for member in students:
            if member.user_id in matched_user_ids:
                continue
            row = existing_rows.get(member.user_id)
            if row is not None and row.manual_override:
                continue
            if row is None:
                row = Attendance(
                    id=uuid.uuid4(),
                    session_id=session.id,
                    user_id=member.user_id,
                    status=AttendanceStatus.ABSENT,
                )
                self.db.add(row)
            row.status = AttendanceStatus.ABSENT
            row.provider = PROVIDER
            row.provider_meeting_id = session.realtimekit_meeting_id
            row.total_attendance_seconds = 0
            row.sync_status = AttendanceSyncStatus.OK
            row.last_synced_at = now
            written += 1
        return written

    # ---------- participant upsert ----------

    def _upsert_participant(
        self,
        session: LiveSession,
        provider_session_id: str,
        raw: dict,
        rules: tuple[int, float, int],
        finalized: bool,
    ) -> tuple[AttendanceParticipant, bool] | None:
        min_seconds, min_percent, late_grace = rules
        participant_id = str(raw.get("id") or raw.get("participant_id") or "").strip()
        if not participant_id:
            return None

        record = self.db.scalar(
            select(AttendanceParticipant).where(
                AttendanceParticipant.session_id == session.id,
                AttendanceParticipant.provider_participant_id == participant_id,
            )
        )
        if record is None:
            record = AttendanceParticipant(
                id=uuid.uuid4(), session_id=session.id, provider_participant_id=participant_id
            )
            self.db.add(record)
            self.db.flush()

        custom_id = raw.get("custom_participant_id") or raw.get("customParticipantId")
        user, member = self._match(session, custom_id)
        if user is None and record.user_id is not None:
            # A prior confident match or a human resolution (resolve_participant)
            # must survive re-syncs, so keep it instead of clearing the link.
            preserved = self.db.get(User, record.user_id)
            if preserved is not None and preserved.is_active:
                user = preserved
                member = self.db.scalar(
                    select(CohortMember).where(
                        CohortMember.cohort_id == session.cohort_id,
                        CohortMember.user_id == preserved.id,
                    )
                )

        joined_at = _parse_dt(raw.get("joined_at") or raw.get("joinedAt"))
        left_at = _parse_dt(raw.get("left_at") or raw.get("leftAt"))
        intervals = self._build_intervals(raw)
        if intervals and intervals[-1][1] is None and left_at:
            intervals[-1] = (intervals[-1][0], left_at, intervals[-1][2])
        total_seconds = self._total_from_intervals(intervals)
        if total_seconds <= 0:
            total_seconds = _duration_to_seconds(raw) or _delta_seconds(joined_at, left_at)
        if total_seconds > 0 and not intervals and joined_at and left_at:
            intervals = [(joined_at, left_at, None)]

        record.provider = PROVIDER
        record.provider_session_id = provider_session_id
        record.custom_participant_id = str(custom_id) if custom_id else None
        record.display_name = _display_name(raw)
        record.user_id = user.id if user else None
        record.first_joined_at = joined_at
        record.last_left_at = left_at
        record.total_attendance_seconds = total_seconds
        record.status = self._status_for(
            session, total_seconds, joined_at, min_seconds, min_percent, late_grace
        )
        record.raw = raw
        record.last_synced_at = _utcnow()
        if record.user_id is None:
            record.sync_status = AttendanceSyncStatus.NEEDS_REVIEW
        elif not finalized:
            record.sync_status = AttendanceSyncStatus.PENDING
        else:
            record.sync_status = AttendanceSyncStatus.OK

        self._replace_intervals(record, intervals)

        written = False
        if user is not None and member is not None and member.role == CohortMemberRole.STUDENT:
            if total_seconds > 0 or finalized:
                written = self._write_attendance(session, user, record, record.status)
        return record, written

    def _provider_session_finalized(self, session: LiveSession, provider_session: dict) -> bool:
        if session.status == LiveSessionStatus.ENDED:
            return True
        if _parse_dt(provider_session.get("ended_at") or provider_session.get("endedAt")):
            return True
        provider_status = str(provider_session.get("status") or "").upper()
        return provider_status not in {"", "LIVE"}

    # ---------- public sync ----------

    def sync_session(self, session: LiveSession) -> SessionAttendanceSyncRow:
        """Reconcile one session's attendance (idempotent)."""
        if session.status == LiveSessionStatus.CANCELLED:
            return SessionAttendanceSyncRow(session_id=session.id, status="skipped", note="cancelled")

        meeting_id = (session.realtimekit_meeting_id or "").strip()
        if not meeting_id or meeting_id.startswith("mock-"):
            return SessionAttendanceSyncRow(
                session_id=session.id, status="skipped", note="no RealtimeKit meeting"
            )

        try:
            provider_session = self.realtimekit.find_session_for_meeting(meeting_id)
        except RealtimeKitError as exc:
            logger.warning("Attendance sync: session lookup failed for %s: %s", session.id, exc)
            return SessionAttendanceSyncRow(session_id=session.id, status="error", note=str(exc))

        if not provider_session:
            # The class may not have started, or the provider has not published it yet.
            return SessionAttendanceSyncRow(
                session_id=session.id, status="pending", note="provider session not found yet"
            )

        provider_session_id = str(provider_session.get("id") or "")
        finalized = self._provider_session_finalized(session, provider_session)

        try:
            participants = self.realtimekit.list_all_session_participants(
                provider_session_id, include_peer_events=True
            )
        except RealtimeKitError as exc:
            logger.warning("Attendance sync: participants fetch failed for %s: %s", session.id, exc)
            return SessionAttendanceSyncRow(session_id=session.id, status="error", note=str(exc))

        rules = self._rules(session)
        matched = unmatched = written = 0
        matched_user_ids: set = set()
        for raw in participants:
            result = self._upsert_participant(session, provider_session_id, raw, rules, finalized)
            if result is None:
                continue
            record, wrote = result
            if record.user_id:
                matched += 1
                matched_user_ids.add(record.user_id)
            else:
                unmatched += 1
            if wrote:
                written += 1

        if finalized:
            written += self._mark_missing_absent(session, matched_user_ids)

        status_value = "needs_review" if unmatched else ("pending" if not finalized else "ok")
        self.db.commit()
        logger.info(
            "Attendance sync session=%s provider_session=%s participants=%s matched=%s "
            "unmatched=%s written=%s status=%s",
            session.id,
            provider_session_id,
            len(participants),
            matched,
            unmatched,
            written,
            status_value,
        )
        return SessionAttendanceSyncRow(
            session_id=session.id,
            status=status_value,
            provider_session_id=provider_session_id or None,
            participants=len(participants),
            matched=matched,
            unmatched=unmatched,
            attendance_written=written,
            last_synced_at=_utcnow(),
        )

    def sync_all(self, *, cohort_id: UUID | None = None) -> AttendanceSyncResult:
        stmt = select(LiveSession).where(LiveSession.status != LiveSessionStatus.CANCELLED)
        if cohort_id:
            stmt = stmt.where(LiveSession.cohort_id == cohort_id)
        sessions = list(self.db.scalars(stmt).all())

        updated = skipped = failed = pending = needs_review = 0
        for session in sessions:
            try:
                result = self.sync_session(session)
            except Exception:  # noqa: BLE001 - one failure must not abort the batch
                logger.exception("Attendance sync failed for session %s", session.id)
                self.db.rollback()
                failed += 1
                continue
            if result.status == "skipped":
                skipped += 1
            elif result.status == "error":
                failed += 1
            elif result.status == "pending":
                pending += 1
            elif result.status == "needs_review":
                needs_review += 1
            else:
                updated += 1
        return AttendanceSyncResult(
            total=len(sessions),
            updated=updated,
            skipped=skipped,
            failed=failed,
            pending=pending,
            needs_review=needs_review,
        )

    # ---------- read + resolve (admin/instructor surfaces) ----------

    def _participant_public(self, record: AttendanceParticipant) -> AttendanceParticipantPublic:
        user = record.user if record.user_id else None
        return AttendanceParticipantPublic(
            id=record.id,
            provider=record.provider,
            provider_session_id=record.provider_session_id,
            provider_participant_id=record.provider_participant_id,
            custom_participant_id=record.custom_participant_id,
            display_name=record.display_name,
            user_id=record.user_id,
            user_name=(user.full_name if user else None),
            user_email=(user.email if user else None),
            matched=record.user_id is not None,
            first_joined_at=record.first_joined_at,
            last_left_at=record.last_left_at,
            total_attendance_seconds=record.total_attendance_seconds,
            status=record.status.value if record.status else None,
            sync_status=record.sync_status.value if record.sync_status else "pending",
            last_synced_at=record.last_synced_at,
            intervals=[
                AttendanceIntervalPublic(
                    joined_at=interval.joined_at,
                    left_at=interval.left_at,
                    duration_seconds=interval.duration_seconds,
                    source=interval.source,
                )
                for interval in record.intervals
            ],
        )

    def session_detail(self, session_id: UUID) -> SessionAttendanceDetail:
        session = self.db.get(LiveSession, session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        participants = list(
            self.db.scalars(
                select(AttendanceParticipant)
                .options(
                    selectinload(AttendanceParticipant.intervals),
                    selectinload(AttendanceParticipant.user),
                )
                .where(AttendanceParticipant.session_id == session_id)
                .order_by(AttendanceParticipant.first_joined_at.asc().nulls_last())
            ).all()
        )
        students = list(
            self.db.scalars(
                select(CohortMember)
                .options(selectinload(CohortMember.user))
                .where(
                    CohortMember.cohort_id == session.cohort_id,
                    CohortMember.role == CohortMemberRole.STUDENT,
                )
            ).all()
        )
        attendance_by_user = {
            row.user_id: row
            for row in self.db.scalars(
                select(Attendance).where(Attendance.session_id == session_id)
            ).all()
        }

        unmatched = sum(1 for p in participants if p.user_id is None)
        matched = len(participants) - unmatched
        last_synced = max(
            (p.last_synced_at for p in participants if p.last_synced_at), default=None
        )
        if unmatched:
            sync_status = AttendanceSyncStatus.NEEDS_REVIEW.value
        elif session.status != LiveSessionStatus.ENDED:
            sync_status = AttendanceSyncStatus.PENDING.value
        else:
            sync_status = AttendanceSyncStatus.OK.value

        expected: list[ExpectedStudentRow] = []
        for member in students:
            row = attendance_by_user.get(member.user_id)
            expected.append(
                ExpectedStudentRow(
                    user_id=member.user_id,
                    full_name=member.user.full_name if member.user else None,
                    email=member.user.email if member.user else "",
                    has_attendance=row is not None,
                    status=row.status.value if row else None,
                    total_attendance_seconds=row.total_attendance_seconds if row else 0,
                    manual_override=bool(row.manual_override) if row else False,
                )
            )

        return SessionAttendanceDetail(
            session_id=session.id,
            session_title=session.title,
            session_started_at=session.starts_at,
            session_ended_at=session.ends_at,
            sync_status=sync_status,
            last_synced_at=last_synced,
            matched_count=matched,
            unmatched_count=unmatched,
            expected_students=expected,
            participants=[self._participant_public(p) for p in participants],
        )

    def resolve_participant(
        self,
        participant_id: UUID,
        *,
        user_id: UUID | None,
        status_value: str | None,
        reason: str | None,
        actor: User | None,
    ) -> AttendanceParticipantPublic:
        """Attach an unmatched participant to a student (or override their status).

        The resulting attendance row is flagged as a manual override so later syncs
        never clobber it, recording who/when/why.
        """
        record = self.db.get(AttendanceParticipant, participant_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")
        session = self.db.get(LiveSession, record.session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        target: User | None = None
        if user_id is not None:
            target = self.db.get(User, user_id)
            if target is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            member = self.db.scalar(
                select(CohortMember).where(
                    CohortMember.cohort_id == session.cohort_id,
                    CohortMember.user_id == user_id,
                )
            )
            if member is None or member.role != CohortMemberRole.STUDENT:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is not a student in this cohort",
                )
            record.user_id = target.id

        if status_value:
            record.status = AttendanceStatus(status_value)

        record.sync_status = (
            AttendanceSyncStatus.OK if record.user_id else AttendanceSyncStatus.NEEDS_REVIEW
        )
        record.last_synced_at = _utcnow()

        if target is not None:
            self._write_manual_resolution(
                session,
                target,
                record,
                status_value=record.status or AttendanceStatus.ATTENDED,
                actor=actor,
                reason=reason,
            )

        self.db.commit()
        self.db.refresh(record)
        return self._participant_public(record)