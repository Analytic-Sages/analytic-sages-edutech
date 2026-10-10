"""Persist concluded live-session recordings to permanent storage.

RealtimeKit's temporary download URLs expire (~7 days), so they are treated as a
transient hand-off only: we ask Cloudflare Stream to fetch the recording and keep
the resulting Stream video uid as the canonical recording. Playback is served via
an enrollment-gated, signed URL generated per request.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.roles import UserRole
from app.models.classroom import (
    Cohort,
    CohortMember,
    LiveSession,
    LiveSessionStatus,
    RecordingStatus,
    SessionRecording,
)
from app.models.user import User
from app.schemas.classroom import SessionRecordingPlayback
from app.schemas.classroom_admin import RecordingCandidateSession, RecordingImportPreview
from app.services.cloudflare_stream import CloudflareStreamError, CloudflareStreamService
from app.services.realtimekit import RealtimeKitService
from app.services.recording_archive import RecordingArchiveError, RecordingArchiveService

logger = logging.getLogger(__name__)

# Roles that may preview any cohort recording without an enrollment.
_STAFF_PREVIEW_ROLES = {UserRole.ADMIN, UserRole.INSTRUCTOR, UserRole.OPERATIONS}


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    text = str(value).strip().strip('"')
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _same_day(a: datetime | None, b: datetime | None) -> bool:
    if not a or not b:
        return False
    a_utc = a.astimezone(timezone.utc) if a.tzinfo else a.replace(tzinfo=timezone.utc)
    b_utc = b.astimezone(timezone.utc) if b.tzinfo else b.replace(tzinfo=timezone.utc)
    return a_utc.date() == b_utc.date()


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
        """Signed Cloudflare Stream URL for a ready Stream video, else None."""
        if (
            recording.provider != "cloudflare_stream"
            or recording.status != RecordingStatus.READY
            or not recording.provider_recording_id
        ):
            return None
        signed = self.stream.signed_playback_url(recording.provider_recording_id)
        if signed:
            return signed
        # No signing key configured → fall back to the (still access-gated) embed URL.
        return recording.recording_url or self.stream.embed_url(recording.provider_recording_id)

    def link_r2_archive(
        self,
        recording_id: str,
        object_key: str,
        *,
        session_id: UUID | None = None,
    ) -> str:
        """Remember which session plays an archived R2 object.

        An explicit session id is the instructor's confirmation from the session
        editor. Without one, an existing link is updated, or the single verified
        candidate is used. A recording is never attached to two sessions, and
        ``realtimekit_meeting_id`` is left unchanged.
        """
        recording_id = recording_id.strip()
        existing = self.db.scalar(
            select(SessionRecording).where(
                SessionRecording.realtimekit_recording_id == recording_id
            )
        )
        if session_id is None:
            if existing is not None:
                self._apply_r2_archive(existing, recording_id, object_key)
                self.db.commit()
                return "updated"
            session = self._unique_archive_session(recording_id)
            if session is None:
                return "skipped"
            self._apply_r2_archive(self.get_or_create(session.id), recording_id, object_key)
            self.db.commit()
            return "linked"

        session = self.db.get(LiveSession, session_id)
        if session is None:
            return "not_found"
        if existing is not None and existing.session_id != session.id:
            return "conflict"
        row = self._get_recording(session.id)
        if (
            row is not None
            and row.realtimekit_recording_id
            and row.realtimekit_recording_id != recording_id
        ):
            return "conflict"
        self._apply_r2_archive(row or self.get_or_create(session.id), recording_id, object_key)
        self.db.commit()
        return "linked"

    def _apply_r2_archive(
        self, recording: SessionRecording, recording_id: str, object_key: str
    ) -> None:
        recording.realtimekit_recording_id = recording_id
        recording.storage_provider = "r2"
        recording.storage_key = object_key
        if not recording.provider_recording_id:
            recording.provider = "r2"
        recording.status = RecordingStatus.READY
        recording.error = None

    def _unique_archive_session(self, recording_id: str) -> LiveSession | None:
        try:
            preview = self.recording_import_preview(recording_id)
        except HTTPException:
            return None
        if preview.ambiguous or len(preview.candidates) != 1:
            return None
        return self.db.get(LiveSession, preview.candidates[0].session_id)

    def _r2_watch_url(self, session: LiveSession, recording: SessionRecording | None) -> str | None:
        """Private R2 playback when Stream cannot build a URL. Never a public object URL."""
        archive = RecordingArchiveService(self.settings, realtimekit=self.realtimekit)
        candidates: list[tuple[str, str]] = []
        if recording is not None and recording.storage_provider == "r2" and recording.storage_key:
            rid = recording.realtimekit_recording_id or ""
            candidates.append((recording.storage_key, rid))
        if recording is not None and recording.realtimekit_recording_id:
            try:
                candidates.append(
                    (archive.object_key(recording.realtimekit_recording_id), recording.realtimekit_recording_id)
                )
            except RecordingArchiveError:
                pass
        seen: set[str] = set()
        for key, _recording_id in candidates:
            if key in seen:
                continue
            seen.add(key)
            url = archive.presigned_watch_url(key)
            if url:
                return url
        if not session.realtimekit_meeting_id:
            return None
        found: list[tuple[str, str, str]] = []
        for item in self.realtimekit.list_recordings(meeting_id=str(session.realtimekit_meeting_id)):
            if str(item.get("status", "")).upper() not in {"UPLOADED", "COMPLETED"}:
                continue
            item_id = str(item.get("id") or item.get("recordingId") or item.get("recording_id") or "")
            if not item_id:
                continue
            try:
                key = archive.object_key(item_id)
            except RecordingArchiveError:
                continue
            url = archive.presigned_watch_url(key)
            if url:
                found.append((item_id, key, url))
        if len(found) != 1:
            return None
        item_id, key, url = found[0]
        self.link_r2_archive(item_id, key, session_id=session.id)
        return url

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

        recording = self._get_recording(session_id)
        stream_url = None
        if (
            recording is not None
            and recording.status == RecordingStatus.READY
            and recording.provider == "cloudflare_stream"
            and recording.provider_recording_id
        ):
            stream_url = self.playback_url(recording)
        # A ready Stream URL wins. Otherwise play the private R2 archive.
        watch_url = stream_url or self._r2_watch_url(session, recording)
        if watch_url:
            uid = (
                recording.provider_recording_id
                if recording is not None and recording.provider == "cloudflare_stream"
                else None
            )
            return SessionRecordingPlayback(
                session_id=session_id,
                status="ready",
                watch_url=watch_url,
                duration_seconds=recording.duration_seconds if recording else None,
                embed_url=self.stream.embed_url(uid) if uid else None,
                hls_url=self.stream.signed_playback_url(uid) if uid and stream_url else None,
            )

        # Manual override (legacy / hand-added link) when no permanent copy exists.
        if session.recording_url:
            return SessionRecordingPlayback(
                session_id=session_id,
                status="ready",
                watch_url=session.recording_url,
            )

        if recording is None:
            return SessionRecordingPlayback(session_id=session_id, status="none")
        return SessionRecordingPlayback(session_id=session_id, status=recording.status.value)

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

    # ---------- importing existing (historical) recordings ----------

    def _merged_recording(self, recording_id: str) -> dict[str, Any]:
        """Combine list + detail responses so we keep the richest metadata."""
        merged: dict[str, Any] = {}
        listing = self.realtimekit.find_recording_in_list(recording_id)
        if listing:
            merged.update(listing)
        detail = self.realtimekit.get_recording(recording_id)
        if detail:
            merged.update({k: v for k, v in detail.items() if v is not None})
        return merged

    def _candidate_sessions(
        self,
        *,
        meeting_id: str | None,
        title: str | None,
        started_at: datetime | None,
    ) -> list[RecordingCandidateSession]:
        """Rank LMS sessions that correspond to a recording. Never guesses.

        Exact RealtimeKit meeting id first. Otherwise an exact title, and the same
        calendar day when the recording has a start time. A shared day alone, or a
        partial title, is not a match.
        """
        sessions = list(
            self.db.scalars(
                select(LiveSession)
                .where(LiveSession.status != LiveSessionStatus.CANCELLED)
                .order_by(LiveSession.starts_at.asc())
            ).all()
        )
        matched: list[RecordingCandidateSession] = []
        seen: set = set()

        def add(session: LiveSession, kind: str) -> None:
            if session.id in seen:
                return
            seen.add(session.id)
            cohort = self.db.get(Cohort, session.cohort_id)
            existing = self._get_recording(session.id)
            matched.append(
                RecordingCandidateSession(
                    session_id=session.id,
                    cohort_id=session.cohort_id,
                    cohort_name=cohort.name if cohort else "",
                    title=session.title,
                    week_label=session.week_label or "",
                    starts_at=session.starts_at,
                    match=kind,
                    has_recording=bool(
                        (existing and existing.provider_recording_id) or session.recording_url
                    ),
                )
            )

        if meeting_id:
            for session in sessions:
                if session.realtimekit_meeting_id and str(session.realtimekit_meeting_id) == str(
                    meeting_id
                ):
                    add(session, "meeting")
        if not matched and title:
            norm = title.strip().casefold()
            for session in sessions:
                if session.title.strip().casefold() != norm:
                    continue
                if started_at and not _same_day(session.starts_at, started_at):
                    continue
                add(session, "title")
        return matched

    def recording_import_preview(self, recording_id: str) -> RecordingImportPreview:
        """Verified metadata + candidate sessions for an existing recording."""
        recording_id = (recording_id or "").strip()
        if not recording_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="recording_id required"
            )

        merged = self._merged_recording(recording_id)
        if not merged:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording not found in RealtimeKit (check the recording ID).",
            )

        meeting_id = self.realtimekit.recording_meeting_id(merged)
        title = self.realtimekit.recording_title(merged)
        started_at = _parse_dt(
            merged.get("started_time")
            or merged.get("startedTime")
            or merged.get("created_at")
            or merged.get("createdAt")
        )
        duration = merged.get("recording_duration") or merged.get("recordingDuration")
        provider_session_id = merged.get("session_id") or merged.get("sessionId")
        status_value = str(merged.get("status") or "").upper()
        download_url = self.realtimekit.recording_download_url(merged)
        expiry = _parse_dt(merged.get("download_url_expiry") or merged.get("downloadUrlExpiry"))

        already_linked = self.db.scalar(
            select(SessionRecording).where(
                SessionRecording.realtimekit_recording_id == recording_id
            )
        )

        candidates = self._candidate_sessions(
            meeting_id=meeting_id, title=title, started_at=started_at
        )
        ambiguous = len(candidates) > 1

        note: str | None = None
        if status_value and status_value not in {"UPLOADED", "COMPLETED"}:
            note = f"Recording status is {status_value}; its download URL may not be ready yet."
        elif not candidates:
            note = (
                "No LMS session matched on meeting id or exact title and date. "
                "Supply a download URL and a reason to recover it manually."
            )
        elif ambiguous:
            note = (
                "Multiple sessions match. Import stays blocked unless you supply a "
                "download URL and a reason for one of those sessions."
            )

        return RecordingImportPreview(
            recording_id=recording_id,
            title=title,
            status=status_value or None,
            started_at=started_at,
            duration_seconds=int(duration) if duration else None,
            meeting_id=meeting_id,
            provider_session_id=str(provider_session_id) if provider_session_id else None,
            has_download_url=bool(download_url),
            download_url_expires_at=expiry,
            already_linked_session_id=already_linked.session_id if already_linked else None,
            candidates=candidates,
            ambiguous=ambiguous,
            note=note,
        )

    def _assert_import_target(
        self,
        session: LiveSession,
        recording_id: str,
        *,
        download_url: str | None,
        reason: str | None,
    ) -> dict[str, Any]:
        """Allow import only for the verified session, or an explicit manual recovery.

        Does not write a meeting id. A shared calendar day alone is not enough.
        """
        manual = bool((download_url or "").strip() and (reason or "").strip())
        merged = self._merged_recording(recording_id)
        if not merged:
            if not manual:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Recording metadata is unavailable. Supply a download URL and a "
                        "reason to recover it manually."
                    ),
                )
            logger.info(
                "Manual recording recovery for session %s recording %s: %s",
                session.id,
                recording_id,
                (reason or "").strip(),
            )
            return merged

        meeting_id = self.realtimekit.recording_meeting_id(merged)
        title = self.realtimekit.recording_title(merged)
        started_at = _parse_dt(
            merged.get("started_time")
            or merged.get("startedTime")
            or merged.get("created_at")
            or merged.get("createdAt")
        )
        candidates = self._candidate_sessions(
            meeting_id=meeting_id, title=title, started_at=started_at
        )
        match_ids = {item.session_id for item in candidates}
        if len(candidates) == 1 and session.id in match_ids:
            return merged
        if manual and (not candidates or session.id in match_ids):
            logger.info(
                "Manual recording recovery for session %s recording %s: %s",
                session.id,
                recording_id,
                (reason or "").strip(),
            )
            return merged
        if candidates and session.id not in match_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This recording's meeting or title matches a different session.",
            )
        if len(candidates) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Multiple sessions match this recording. Supply a download URL and a "
                    "reason to import it onto one of them."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No LMS session matched this recording on meeting id or exact title and date. "
                "Supply a download URL and a reason to attach it manually."
            ),
        )

    def import_recording(
        self,
        session: LiveSession,
        *,
        recording_id: str,
        download_url: str | None = None,
        reason: str | None = None,
        replace_existing: bool = False,
    ) -> SessionRecording:
        """Attach an existing RealtimeKit recording to one session and persist it.

        Idempotent and duplicate-safe: reuses the session's recording row and refuses
        to link the same RealtimeKit recording id to two sessions. The temporary
        RealtimeKit URL is only used to hand the file to Cloudflare Stream and is
        never stored. Does not change attendance or ``realtimekit_meeting_id``.
        """
        recording_id = (recording_id or "").strip()
        if not recording_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="recording_id required"
            )

        other = self.db.scalar(
            select(SessionRecording).where(
                SessionRecording.realtimekit_recording_id == recording_id,
                SessionRecording.session_id != session.id,
            )
        )
        if other is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This RealtimeKit recording is already linked to another session.",
            )

        recording = self._get_recording(session.id)
        if (
            recording
            and (recording.provider_recording_id or recording.realtimekit_recording_id)
            and recording.realtimekit_recording_id != recording_id
            and not replace_existing
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This session is already linked to a different RealtimeKit recording.",
            )

        # Already handed off to permanent storage → refresh status only (no duplicate).
        if (
            recording
            and recording.provider_recording_id
            and recording.status != RecordingStatus.FAILED
            and recording.realtimekit_recording_id == recording_id
        ):
            return self.reconcile(recording)

        merged = self._assert_import_target(
            session,
            recording_id,
            download_url=download_url,
            reason=reason,
        )
        if not download_url and merged:
            download_url = self.realtimekit.recording_download_url(merged)
        if not download_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No downloadable URL is available for this recording yet.",
            )

        # Copy first; only switch the class's primary recording after the new
        # asset has been accepted by permanent storage. A failed replacement
        # must leave the current recording link untouched.
        try:
            uid = self.stream.copy_from_url(
                url=download_url,
                meta={
                    "session_id": str(session.id),
                    "cohort_id": str(session.cohort_id),
                    "title": session.title,
                    "source": "realtimekit_import",
                    "realtimekit_recording_id": recording_id,
                },
                require_signed=self.settings.cloudflare_stream_signing_configured,
            )
        except CloudflareStreamError as exc:
            if recording is None:
                recording = self.get_or_create(session.id)
                recording.status = RecordingStatus.FAILED
                recording.error = str(exc)
                self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Cloudflare Stream could not fetch the recording: {exc}",
            ) from exc

        recording = recording or self.get_or_create(session.id)
        recording.realtimekit_recording_id = recording_id
        recording.provider = "cloudflare_stream"
        recording.provider_recording_id = uid
        recording.storage_provider = "cloudflare_stream"
        recording.storage_key = uid
        recording.status = RecordingStatus.PROCESSING
        recording.error = None
        self.db.commit()
        return self.reconcile(recording)