"""Admin CRUD for live classroom sessions.

Lets staff create / edit / cancel sessions from the dashboard without a developer,
reusing the classroom models and the same phase rules students see.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.classroom import (
    Cohort,
    CohortMember,
    LiveSession,
    LiveSessionStatus,
    LiveSessionType,
    RecordingStatus,
)
from app.schemas.classroom_admin import (
    AdminCohortOption,
    AdminLiveSessionCreate,
    AdminLiveSessionRow,
    AdminLiveSessionUpdate,
    AdminRecordingSyncResult,
    RecordingImportPreview,
    RecordingImportRequest,
)
from app.schemas.attendance import (
    AttendanceParticipantPublic,
    AttendanceResolveRequest,
    AttendanceSyncResult,
    SessionAttendanceDetail,
    SessionAttendanceSyncRow,
)
from app.models.user import User
from app.services.attendance import AttendanceSyncService
from app.services.classroom import ClassroomService
from app.services.meeting_close import MeetingCloseService
from app.services.recordings import RecordingsService


class ClassroomAdminService:
    def __init__(self, db: Session, classroom: ClassroomService) -> None:
        self.db = db
        self.classroom = classroom
        self.recordings = RecordingsService(db, classroom.settings)
        self.attendance = AttendanceSyncService(db, classroom.settings)

    def list_cohorts(self) -> list[AdminCohortOption]:
        cohorts = list(
            self.db.scalars(
                select(Cohort)
                .options(joinedload(Cohort.course))
                .order_by(Cohort.starts_at.desc().nulls_last(), Cohort.name.asc())
            )
            .unique()
            .all()
        )
        counts = dict(
            self.db.execute(
                select(LiveSession.cohort_id, func.count()).group_by(LiveSession.cohort_id)
            ).all()
        )
        return [
            AdminCohortOption(
                id=cohort.id,
                name=cohort.name,
                slug=cohort.slug,
                status=cohort.status.value,
                course_title=cohort.course.title if cohort.course else None,
                sessions_count=int(counts.get(cohort.id, 0)),
            )
            for cohort in cohorts
        ]

    def _member_count(self, cohort_id: UUID) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(CohortMember)
                .where(CohortMember.cohort_id == cohort_id)
            )
            or 0
        )

    def _row(self, session: LiveSession) -> AdminLiveSessionRow:
        cohort = self.db.get(Cohort, session.cohort_id)
        recording = self.recordings._get_recording(session.id)
        if recording is not None and recording.status == RecordingStatus.READY:
            recording_status = "ready"
        elif session.recording_url:
            recording_status = "ready"
        elif recording is not None:
            recording_status = recording.status.value
        else:
            recording_status = "none"
        return AdminLiveSessionRow(
            id=session.id,
            cohort_id=session.cohort_id,
            cohort_name=cohort.name if cohort else "",
            cohort_slug=cohort.slug if cohort else "",
            title=session.title,
            week_label=session.week_label,
            session_number=session.session_number,
            session_type=session.session_type.value,
            objectives=list(session.objectives or []),
            resources=list(session.resources or []),
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
            phase=self.classroom._effective_phase(session),
            recording_url=session.recording_url,
            recording_status=recording_status,
            member_count=self._member_count(session.cohort_id),
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    def list_sessions(
        self, *, cohort_id: UUID | None = None, limit: int = 500
    ) -> list[AdminLiveSessionRow]:
        """Schedule order (earliest first) so the full plan reads Week 1 → Week 10."""
        stmt = select(LiveSession).order_by(
            LiveSession.starts_at.asc().nulls_last(), LiveSession.session_number.asc()
        )
        if cohort_id:
            stmt = stmt.where(LiveSession.cohort_id == cohort_id)
        sessions = list(self.db.scalars(stmt.limit(limit)).all())
        return [self._row(session) for session in sessions]

    def _validate_window(self, starts_at, ends_at) -> None:
        if ends_at <= starts_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session end time must be after the start time",
            )

    def _assert_unique_slot(
        self, *, cohort_id: UUID, session_type: str, session_number: int, exclude_id: UUID | None
    ) -> None:
        stmt = select(LiveSession).where(
            LiveSession.cohort_id == cohort_id,
            LiveSession.session_type == LiveSessionType(session_type),
            LiveSession.session_number == session_number,
        )
        if exclude_id:
            stmt = stmt.where(LiveSession.id != exclude_id)
        if self.db.scalar(stmt):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"A {session_type.replace('_', ' ')} session #{session_number} already "
                    "exists for this cohort"
                ),
            )

    def create_session(self, payload: AdminLiveSessionCreate) -> AdminLiveSessionRow:
        cohort = self.db.get(Cohort, payload.cohort_id)
        if not cohort:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")
        self._validate_window(payload.starts_at, payload.ends_at)
        self._assert_unique_slot(
            cohort_id=payload.cohort_id,
            session_type=payload.session_type,
            session_number=payload.session_number,
            exclude_id=None,
        )
        session = LiveSession(
            cohort_id=payload.cohort_id,
            title=payload.title,
            week_label=payload.week_label,
            session_number=payload.session_number,
            session_type=LiveSessionType(payload.session_type),
            objectives=list(payload.objectives),
            resources=[r.model_dump() for r in payload.resources],
            assignment_summary=payload.assignment_summary,
            description=payload.description,
            timezone=payload.timezone or "UTC",
            meeting_url=payload.meeting_url,
            instructor_user_id=payload.instructor_user_id,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            status=LiveSessionStatus.SCHEDULED,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return self._row(session)

    def update_session(
        self, session_id: UUID, payload: AdminLiveSessionUpdate
    ) -> AdminLiveSessionRow:
        session = self.db.get(LiveSession, session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        data = payload.model_dump(exclude_unset=True)
        starts_at = data.get("starts_at", session.starts_at)
        ends_at = data.get("ends_at", session.ends_at)
        self._validate_window(starts_at, ends_at)

        session_type = data.get("session_type", session.session_type.value)
        session_number = data.get("session_number", session.session_number)
        if "session_type" in data or "session_number" in data:
            self._assert_unique_slot(
                cohort_id=session.cohort_id,
                session_type=session_type,
                session_number=session_number,
                exclude_id=session.id,
            )

        if "title" in data:
            session.title = data["title"]
        if "week_label" in data:
            session.week_label = data["week_label"]
        if "session_number" in data:
            session.session_number = data["session_number"]
        if "session_type" in data:
            session.session_type = LiveSessionType(data["session_type"])
        if "objectives" in data:
            session.objectives = list(data["objectives"])
        if "resources" in data:
            session.resources = [
                r.model_dump() if hasattr(r, "model_dump") else r for r in data["resources"]
            ]
        if "assignment_summary" in data:
            session.assignment_summary = data["assignment_summary"]
        if "description" in data:
            session.description = data["description"]
        if "timezone" in data:
            session.timezone = data["timezone"]
        if "meeting_url" in data:
            session.meeting_url = data["meeting_url"]
        if "instructor_user_id" in data:
            session.instructor_user_id = data["instructor_user_id"]
        if "starts_at" in data:
            session.starts_at = data["starts_at"]
        if "ends_at" in data:
            session.ends_at = data["ends_at"]
        if "status" in data:
            session.status = LiveSessionStatus(data["status"])
        if "recording_url" in data:
            session.recording_url = data["recording_url"]

        now = datetime.now(timezone.utc)
        ends_at = session.ends_at
        if ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)
        reopened = session.status in {LiveSessionStatus.SCHEDULED, LiveSessionStatus.LIVE} and ends_at > now
        if reopened:
            session.realtimekit_closed_at = None

        self.db.commit()
        self.db.refresh(session)
        if not reopened:
            self._close_provider_meeting(session)
            self.db.refresh(session)
        return self._row(session)

    def cancel_session(self, session_id: UUID) -> AdminLiveSessionRow:
        session = self.db.get(LiveSession, session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        session.status = LiveSessionStatus.CANCELLED
        self.db.commit()
        self.db.refresh(session)
        self._close_provider_meeting(session)
        self.db.refresh(session)
        return self._row(session)

    def _close_provider_meeting(self, session: LiveSession) -> None:
        MeetingCloseService(
            self.db, self.classroom.settings, realtimekit=self.classroom.realtimekit
        ).close_session(session)

    def delete_session(self, session_id: UUID) -> None:
        session = self.db.get(LiveSession, session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        self.db.delete(session)
        self.db.commit()

    # ---------- recordings ----------

    def sync_recording(self, session_id: UUID) -> AdminLiveSessionRow:
        """Persist the session's RealtimeKit recording to permanent storage."""
        session = self.db.get(LiveSession, session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        self.recordings.sync_session(session)
        self.db.refresh(session)
        return self._row(session)

    def sync_recordings(self, *, cohort_id: UUID | None = None) -> AdminRecordingSyncResult:
        """Persist recordings for sessions (optionally one cohort)."""
        summary = self.recordings.sync_all(cohort_id=cohort_id)
        return AdminRecordingSyncResult(**summary)

    def preview_recording_import(self, recording_id: str) -> RecordingImportPreview:
        """Verified metadata + candidate sessions for an existing recording."""
        return self.recordings.recording_import_preview(recording_id)

    def import_recording(
        self, session_id: UUID, payload: RecordingImportRequest
    ) -> AdminLiveSessionRow:
        """Attach an existing RealtimeKit recording to a specific historical session."""
        session = self.db.get(LiveSession, session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        self.recordings.import_recording(
            session,
            recording_id=payload.recording_id,
            download_url=payload.download_url,
            reason=payload.reason,
            replace_existing=payload.replace_existing,
        )
        self.db.refresh(session)
        return self._row(session)

    # ---------- attendance (RealtimeKit reconciliation) ----------

    def sync_attendance(self, session_id: UUID) -> SessionAttendanceSyncRow:
        """Reconcile one session's attendance from RealtimeKit."""
        session = self.db.get(LiveSession, session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return self.attendance.sync_session(session)

    def sync_attendances(self, *, cohort_id: UUID | None = None) -> AttendanceSyncResult:
        """Reconcile attendance for sessions (optionally one cohort)."""
        return self.attendance.sync_all(cohort_id=cohort_id)

    def session_attendance(self, session_id: UUID) -> SessionAttendanceDetail:
        """Expected vs matched/unmatched participants for a session."""
        return self.attendance.session_detail(session_id)

    def resolve_attendance_participant(
        self, participant_id: UUID, payload: AttendanceResolveRequest, actor: User | None = None
    ) -> AttendanceParticipantPublic:
        """Attach an unmatched participant to a student (manual override)."""
        return self.attendance.resolve_participant(
            participant_id,
            user_id=payload.user_id,
            status_value=payload.status,
            reason=payload.reason,
            actor=actor,
        )