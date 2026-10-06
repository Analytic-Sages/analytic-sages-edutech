from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)


class RealtimeKitError(Exception):
    """Raised when Cloudflare RealtimeKit API calls fail."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class RealtimeKitService:
    """Authorize live classroom participants via Cloudflare RealtimeKit.

    When credentials are missing, operates in mock mode so local/dev classroom
    UI can still be exercised without Cloudflare keys.
    """

    API_BASE = "https://api.cloudflare.com/client/v4"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def configured(self) -> bool:
        return bool(
            self.settings.cloudflare_account_id
            and self.settings.cloudflare_api_token
            and self.settings.realtimekit_app_id
        )

    @property
    def mode(self) -> str:
        return "live" if self.configured else "mock"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.cloudflare_api_token}",
            "Content-Type": "application/json",
        }

    def _meetings_url(self, meeting_id: str | None = None) -> str:
        base = (
            f"{self.API_BASE}/accounts/{self.settings.cloudflare_account_id}"
            f"/realtime/kit/{self.settings.realtimekit_app_id}/meetings"
        )
        if meeting_id:
            return f"{base}/{meeting_id}"
        return base

    def create_meeting(self, *, title: str) -> str:
        if not self.configured:
            return f"mock-meeting-{title[:40].replace(' ', '-').lower()}"

        payload = {
            "title": title,
            "record_on_start": self.settings.realtimekit_record_on_start,
            "persist_chat": True,
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self._meetings_url(),
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            logger.exception("RealtimeKit create_meeting failed")
            raise RealtimeKitError("Failed to create RealtimeKit meeting") from exc

        payload_data = data.get("data")
        if isinstance(payload_data, dict):
            meeting_id = payload_data.get("id") or (payload_data.get("meeting") or {}).get("id")
        else:
            meeting_id = data.get("id")
        if not meeting_id:
            raise RealtimeKitError(f"Unexpected create_meeting response: {data}")
        return str(meeting_id)

    def _recordings_url(self, recording_id: str | None = None) -> str:
        base = (
            f"{self.API_BASE}/accounts/{self.settings.cloudflare_account_id}"
            f"/realtime/kit/{self.settings.realtimekit_app_id}/recordings"
        )
        return f"{base}/{recording_id}" if recording_id else base

    def list_recordings(self, *, meeting_id: str) -> list[dict[str, Any]]:
        """Return recordings for a meeting (empty when not configured/no recordings).

        RealtimeKit keeps composite recordings for ~7 days; each item carries a
        ``status`` and, once UPLOADED, a ``downloadUrl`` (or ``download_url``).
        """
        if not meeting_id or str(meeting_id).startswith("mock-"):
            return []
        return self.list_app_recordings(meeting_id=meeting_id)

    def list_app_recordings(
        self,
        *,
        meeting_id: str | None = None,
        search: str | None = None,
        status: str | list[str] | None = None,
        expired: bool | None = None,
        page_no: int = 1,
        per_page: int = 200,
    ) -> list[dict[str, Any]]:
        """List the app's recordings, optionally filtered (empty in mock mode).

        Documented query params: ``meeting_id``, ``search`` (meeting id or title),
        ``status`` (array), ``expired``, ``page_no``, ``per_page``.
        """
        if not self.configured:
            return []
        params: dict[str, Any] = {"page_no": page_no, "per_page": per_page}
        if meeting_id:
            params["meeting_id"] = str(meeting_id)
        if search:
            params["search"] = search
        if status:
            params["status"] = status
        if expired is not None:
            params["expired"] = "true" if expired else "false"
        try:
            data = self._get_json(self._recordings_url(), params=params)
        except RealtimeKitError:
            logger.exception("RealtimeKit list_app_recordings failed")
            return []
        return self._recording_items(data)

    @staticmethod
    def _recording_items(data: dict[str, Any]) -> list[dict[str, Any]]:
        body = data.get("data") if isinstance(data.get("data"), (list, dict)) else data
        if isinstance(body, dict):
            items = body.get("recordings") or body.get("items") or []
        else:
            items = body
        return [item for item in items if isinstance(item, dict)]

    def get_recording(self, recording_id: str) -> dict[str, Any] | None:
        """Fetch details of a single recording by its RealtimeKit recording id.

        ``GET …/recordings/{recording_id}`` — returns the recording's ``session_id``
        (provider session), ``download_url`` (temporary), status and timings. Returns
        ``None`` when the recording does not exist (404).
        """
        if not self.configured or not recording_id:
            return None
        try:
            data = self._get_json(self._recordings_url(recording_id))
        except RealtimeKitError as exc:
            if exc.status_code == 404:
                return None
            raise
        body = data.get("data") if isinstance(data.get("data"), dict) else data
        return body if isinstance(body, dict) else None

    def find_recording_in_list(
        self, recording_id: str, *, max_pages: int = 25
    ) -> dict[str, Any] | None:
        """Locate a recording in the app's recordings list.

        The list (unlike the single-recording GET) includes the nested ``meeting``
        object and a title, which are needed to match a recording to an LMS session.
        """
        if not self.configured or not recording_id:
            return None
        page = 1
        while page <= max_pages:
            items = self.list_app_recordings(page_no=page)
            for item in items:
                item_id = item.get("id") or item.get("recordingId") or item.get("recording_id")
                if str(item_id or "") == str(recording_id):
                    return item
            if len(items) < 200:
                break
            page += 1
        return None

    def recording_meeting_id(self, recording: dict[str, Any]) -> str | None:
        """Resolve a recording's meeting id using only verified fields.

        Order: the nested ``meeting.id`` from the recordings list, then any direct
        ``meeting_id``, else resolve the recording's provider ``session_id`` through
        the Sessions API to its ``associated_id`` (the meeting id). The recording id
        is never treated as a meeting id.
        """
        meeting = recording.get("meeting")
        if isinstance(meeting, dict):
            meeting_id = meeting.get("id") or meeting.get("meetingId")
            if meeting_id:
                return str(meeting_id)
        direct = recording.get("meeting_id") or recording.get("meetingId")
        if direct:
            return str(direct)
        session_id = recording.get("session_id") or recording.get("sessionId")
        if not session_id:
            return None
        try:
            sessions = self.list_sessions(per_page=100)["sessions"]
        except RealtimeKitError:
            return None
        for session in sessions:
            if str(session.get("id")) == str(session_id):
                associated = session.get("associated_id") or session.get("associatedId")
                return str(associated) if associated else None
        return None

    @staticmethod
    def recording_title(recording: dict[str, Any]) -> str | None:
        meeting = recording.get("meeting")
        if isinstance(meeting, dict) and meeting.get("title"):
            return str(meeting["title"])
        title = (
            recording.get("title")
            or recording.get("output_file_name")
            or recording.get("outputFileName")
        )
        return str(title) if title else None

    @staticmethod
    def recording_download_url(recording: dict[str, Any]) -> str | None:
        url = (
            recording.get("download_url")
            or recording.get("downloadUrl")
            or recording.get("audio_download_url")
            or recording.get("audioDownloadUrl")
        )
        return str(url) if url else None

    def latest_download_url(self, *, meeting_id: str) -> str | None:
        """Newest UPLOADED recording's download URL for a meeting, if any."""
        recordings = self.list_recordings(meeting_id=meeting_id)
        ready = [
            item
            for item in recordings
            if str(item.get("status", "")).upper() in {"UPLOADED", "COMPLETED"}
        ]
        # Prefer the most recently created recording.
        ready.sort(key=lambda item: str(item.get("createdAt") or item.get("created_at") or ""), reverse=True)
        for item in ready:
            url = self.recording_download_url(item)
            if url:
                return str(url)
        return None

    def start_recording(self, *, meeting_id: str) -> bool:
        """Explicitly start recording a meeting (idempotent best-effort)."""
        if not self.configured or not meeting_id or str(meeting_id).startswith("mock-"):
            return False
        url = f"{self._meetings_url(meeting_id)}/recording/start"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    url,
                    headers=self._headers(),
                    json={"allow_livestream": False, "allow_transcript": False},
                )
                if response.status_code >= 400:
                    logger.error(
                        "RealtimeKit start_recording failed: %s %s",
                        response.status_code,
                        response.text,
                    )
                    return False
                return True
        except httpx.HTTPError:
            logger.exception("RealtimeKit start_recording failed")
            return False

    def add_participant(
        self,
        *,
        meeting_id: str,
        custom_participant_id: str,
        name: str,
        preset_name: str,
    ) -> dict[str, Any]:
        if not self.configured:
            return {
                "id": f"mock-participant-{custom_participant_id}",
                "token": f"mock-token-{custom_participant_id}",
                "preset_name": preset_name,
            }

        payload = {
            "name": name,
            "preset_name": preset_name,
            "custom_participant_id": custom_participant_id,
        }
        url = f"{self._meetings_url(meeting_id)}/participants"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=self._headers(), json=payload)
                # If participant already exists, try refresh via list+token is complex;
                # surface a clear error for now.
                if response.status_code >= 400:
                    logger.error(
                        "RealtimeKit add_participant failed: %s %s",
                        response.status_code,
                        response.text,
                    )
                    raise RealtimeKitError(
                        f"Failed to add RealtimeKit participant ({response.status_code})",
                        status_code=response.status_code,
                    )
                data = response.json()
        except httpx.HTTPError as exc:
            logger.exception("RealtimeKit add_participant failed")
            raise RealtimeKitError("Failed to add RealtimeKit participant") from exc

        body = data.get("data") if isinstance(data.get("data"), dict) else data
        token = body.get("token") if isinstance(body, dict) else None
        if not token:
            raise RealtimeKitError(f"Unexpected add_participant response: {data}")
        return body

    # ---------- attendance: sessions + participants ----------
    #
    # RealtimeKit exposes post-session attendance through the Sessions API:
    #   GET /accounts/{acct}/realtime/kit/{app}/sessions
    #   GET /accounts/{acct}/realtime/kit/{app}/sessions/{session_id}/participants
    # Each participant carries id, custom_participant_id, display_name, duration,
    # joined_at, left_at and (optionally) peer_events for reconnects.

    def _sessions_url(self, suffix: str = "") -> str:
        base = (
            f"{self.API_BASE}/accounts/{self.settings.cloudflare_account_id}"
            f"/realtime/kit/{self.settings.realtimekit_app_id}/sessions"
        )
        return f"{base}{suffix}"

    def _get_json(
        self, url: str, *, params: dict[str, Any] | None = None, attempts: int = 3
    ) -> dict[str, Any]:
        """GET JSON with bounded retry/backoff on transient failures.

        Retries timeouts/connection errors and 5xx/429; fails fast on other 4xx.
        """
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(url, headers=self._headers(), params=params)
            except httpx.HTTPError as exc:
                last_error = exc
                logger.warning(
                    "RealtimeKit GET %s failed (attempt %s/%s): %s", url, attempt, attempts, exc
                )
            else:
                if response.status_code in {429, 500, 502, 503, 504}:
                    last_error = RealtimeKitError(
                        f"RealtimeKit returned {response.status_code}", status_code=response.status_code
                    )
                    logger.warning(
                        "RealtimeKit GET %s returned %s (attempt %s/%s)",
                        url,
                        response.status_code,
                        attempt,
                        attempts,
                    )
                elif response.status_code >= 400:
                    raise RealtimeKitError(
                        f"RealtimeKit GET failed ({response.status_code}): {response.text[:200]}",
                        status_code=response.status_code,
                    )
                else:
                    return response.json()
            if attempt < attempts:
                time.sleep(0.5 * attempt)
        raise RealtimeKitError("RealtimeKit GET failed after retries") from last_error

    def list_sessions(
        self, *, associated_id: str | None = None, page_no: int = 1, per_page: int = 50
    ) -> dict[str, Any]:
        """Return ``{"sessions": [...], "paging": {...}}`` (empty in mock mode)."""
        if not self.configured:
            return {"sessions": [], "paging": {}}
        params: dict[str, Any] = {"page_no": page_no, "per_page": per_page}
        if associated_id:
            params["associated_id"] = str(associated_id)
        data = self._get_json(self._sessions_url(), params=params)
        body = data.get("data") if isinstance(data.get("data"), dict) else data
        return {
            "sessions": list(body.get("sessions") or []),
            "paging": dict(body.get("paging") or data.get("paging") or {}),
        }

    def find_session_for_meeting(self, meeting_id: str) -> dict[str, Any] | None:
        """The most recent provider session recorded against a meeting id."""
        sessions = self.list_meeting_sessions(meeting_id)
        if not sessions:
            return None
        sessions = sorted(
            sessions,
            key=lambda s: str(s.get("started_at") or s.get("created_at") or ""),
            reverse=True,
        )
        return sessions[0]

    def list_meeting_sessions(self, meeting_id: str, *, max_pages: int = 10) -> list[dict[str, Any]]:
        """Every RealtimeKit session for a meeting, oldest pages included."""
        if not meeting_id or not self.configured:
            return []
        collected: list[dict[str, Any]] = []
        page = 1
        while page <= max_pages:
            payload = self.list_sessions(associated_id=str(meeting_id), page_no=page, per_page=100)
            items = payload["sessions"]
            collected.extend(items)
            if len(items) < 100:
                break
            page += 1
        return collected

    def list_session_participants(
        self,
        session_id: str,
        *,
        page_no: int = 1,
        per_page: int = 200,
        include_peer_events: bool = True,
    ) -> dict[str, Any]:
        """Return ``{"participants": [...], "paging": {...}}`` (empty in mock mode)."""
        if not self.configured:
            return {"participants": [], "paging": {}}
        params: dict[str, Any] = {"page_no": page_no, "per_page": per_page}
        if include_peer_events:
            params["include_peer_events"] = "true"
        data = self._get_json(self._sessions_url(f"/{session_id}/participants"), params=params)
        body = data.get("data") if isinstance(data.get("data"), dict) else data
        return {
            "participants": list(body.get("participants") or []),
            "paging": dict(body.get("paging") or {}),
        }

    def list_all_session_participants(
        self, session_id: str, *, include_peer_events: bool = True, max_pages: int = 20
    ) -> list[dict[str, Any]]:
        """Page through every participant in a session."""
        per_page = 200
        collected: list[dict[str, Any]] = []
        page = 1
        while page <= max_pages:
            result = self.list_session_participants(
                session_id, page_no=page, per_page=per_page, include_peer_events=include_peer_events
            )
            participants = result["participants"]
            collected.extend(participants)
            if not participants:
                break
            total = (result.get("paging") or {}).get("total_count")
            if total is not None and len(collected) >= int(total):
                break
            if total is None and len(participants) < per_page:
                break
            page += 1
        return collected

    def get_session_participant(
        self, session_id: str, participant_id: str, *, include_peer_events: bool = True
    ) -> dict[str, Any] | None:
        """Single participant details (with optional peer events) or None."""
        if not self.configured:
            return None
        params = {"include_peer_events": "true"} if include_peer_events else None
        data = self._get_json(
            self._sessions_url(f"/{session_id}/participants/{participant_id}"), params=params
        )
        body = data.get("data") if isinstance(data.get("data"), dict) else data
        participant = body.get("participant")
        return participant if isinstance(participant, dict) else None
