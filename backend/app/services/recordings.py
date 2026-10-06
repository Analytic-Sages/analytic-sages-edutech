"""Persist concluded live-session recordings to permanent storage.

RealtimeKit's temporary download URLs expire (~7 days), so they are treated as a
transient hand-off only: we ask Cloudflare Stream to fetch the recording and keep
the resulting Stream video uid as the canonical recording. Playback is served via
an enrollment-gated, signed URL generated per request.
"""

from __future__ import annotations

import logging
import uuid
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.roles import UserRole
from app.models.classroom import (
    CohortMember,
    LiveSession,
    LiveSessionStatus,
    RecordingStatus,
    SessionRecording,
)
from app.models.user import User
from app.schemas.classroom import SessionRecordingPlayback
from app.services.cloudflare_stream import CloudflareStreamError, CloudflareStreamService
from app.services.realtimekit import RealtimeKitService

logger = logging.getLogger(__name__)

# Roles that may preview any cohort recording without an enrollment.
_STAFF_PREVIEW_ROLES = {UserRole.ADMIN, UserRole.INSTRUCTOR, UserRole.OPERATIONS}


class RecordingsService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.realtimekit = RealtimeKitService(settings)
        self.stream = CloudflareStreamService(settings)

    def _get_recording(self, session_id: UUID) -> SessionRecording | None:
        return self.db.scalar(
            select(SessionRecording).where(SessionRecording.session_id == session_id)
        )

    def get_or_create(self, session_id: UUID) -> SessionRecording:
        recording = self._get_recording(session_id)
        if recording is None:
            recording = SessionRecording(id=uuid.uuid4(), session_id=session_id)
            self.db.add(recording)
            self.db.flush()
        return recording

    def sync_session(self, session: LiveSession) -> SessionRecording | None:
        """Ensure a permanent recording exists for a concluded session.

        Pulls the newest RealtimeKit recording URL then hands it to Cloudflare
        Stream (which fetches it) and records the Stream uid (status=processing).
        Idempotent: re-running before the video is ready just triggers a reconcile.
        """
        if not session.realtimekit_meeting_id:
            return None

        recording = self.get_or_create(session.id)

        # Already handed off to permanent storage → just refresh its status.
        if recording.provider_recording_id and recording.status != RecordingStatus.FAILED:
            return self.reconcile(recording)

        download_url = self.realtimekit.latest_download_url(
            meeting_id=str(session.realtimekit_meeting_id)
        )
        if not download_url:
            return recording

        try:
            uid = self.stream.copy_from_url(
                url=download_url,
                meta={
                    "session_id": str(session.id),
                    "cohort_id": str(session.cohort_id),
                    "title": session.title,
                },
                require_signed=self.settings.cloudflare_stream_signing_configured,
            )
        except CloudflareStreamError as exc:
            recording.status = RecordingStatus.FAILED
            recording.error = str(exc)
            self.db.commit()
            logger.warning("Recording copy failed for session %s: %s", session.id, exc)
            return recording

        recording.provider = "cloudflare_stream"
        recording.provider_recording_id = uid
        recording.storage_provider = "cloudflare_stream"
        recording.storage_key = uid
        recording.status = RecordingStatus.PROCESSING
        recording.error = None
        self.db.commit()
        return self.reconcile(recording)

    def reconcile(self, recording: SessionRecording) -> SessionRecording:
        """Refresh a recording's status/duration from Cloudflare Stream."""
        if not recording.provider_recording_id:
            return recording
        try:
            video = self.stream.get_video(recording.provider_recording_id)
        except CloudflareStreamError:
            return recording

        if video.status in {"ready"}:
            recording.status = RecordingStatus.READY
            recording.duration_seconds = video.duration_seconds
            recording.recording_url = self.stream.embed_url(recording.provider_recording_id)
        elif video.status == "error":
            recording.status = RecordingStatus.FAILED
        self.db.commit()
        return recording

    def playback_url(self, recording: SessionRecording) -> str | None:
        """Signed (private) playback URL for a ready recording, else None."""
        if recording.status != RecordingStatus.READY or not recording.provider_recording_id:
            return None
        signed = self.stream.signed_playback_url(recording.provider_recording_id)
        if signed:
            return signed
        # No signing key configured → fall back to the (still access-gated) embed URL.
        return recording.recording_url or self.stream.embed_url(recording.provider_recording_id)

    def playback(self, user: User, cohort_id: UUID, session_id: UUID) -> SessionRecordingPlayback:
        """Access-gated playback for a session's permanent recording.

        Students must be enrolled in the cohort; instructors/admins/ops may preview
        any cohort. A signed URL (or the gated embed URL) is generated per request.
        """
        session = self.db.get(LiveSession, session_id)
        if not session or session.cohort_id != cohort_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        member = self.db.scalar(
            select(CohortMember).where(
                CohortMember.cohort_id == cohort_id,
                CohortMember.user_id == user.id,
            )
        )
        is_member = member is not None
        if not is_member and user.role not in _STAFF_PREVIEW_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in this cohort",
            )

        # Manual override (legacy / hand-added link) wins when present.
        if session.recording_url:
            return SessionRecordingPlayback(
                session_id=session_id,
                status="ready",
                watch_url=session.recording_url,
            )

        recording = self._get_recording(session_id)
        if recording is None:
            return SessionRecordingPlayback(session_id=session_id, status="none")
        if recording.status != RecordingStatus.READY:
            return SessionRecordingPlayback(session_id=session_id, status=recording.status.value)

        uid = recording.provider_recording_id
        return SessionRecordingPlayback(
            session_id=session_id,
            status="ready",
            watch_url=self.playback_url(recording),
            duration_seconds=recording.duration_seconds,
            embed_url=self.stream.embed_url(uid) if uid else None,
            hls_url=self.stream.signed_playback_url(uid) if uid else None,
        )

    def sync_all(self, *, cohort_id: UUID | None = None) -> dict[str, int]:
        stmt = select(LiveSession).where(LiveSession.status != LiveSessionStatus.CANCELLED)
        if cohort_id:
            stmt = stmt.where(LiveSession.cohort_id == cohort_id)
        sessions = list(self.db.scalars(stmt).all())

        updated = skipped = failed = 0
        for session in sessions:
            try:
                recording = self.sync_session(session)
            except Exception:  # noqa: BLE001 - one failure must not abort the batch
                failed += 1
                continue
            if recording is None:
                skipped += 1
            elif recording.status == RecordingStatus.FAILED:
                failed += 1
            else:
                updated += 1
        return {"total": len(sessions), "updated": updated, "skipped": skipped, "failed": failed}