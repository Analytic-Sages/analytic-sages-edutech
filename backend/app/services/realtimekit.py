from __future__ import annotations

import logging
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

    def _recordings_url(self) -> str:
        return (
            f"{self.API_BASE}/accounts/{self.settings.cloudflare_account_id}"
            f"/realtime/kit/{self.settings.realtimekit_app_id}/recordings"
        )

    def list_recordings(self, *, meeting_id: str) -> list[dict[str, Any]]:
        """Return recordings for a meeting (empty when not configured/no recordings).

        RealtimeKit keeps composite recordings for ~7 days; each item carries a
        ``status`` and, once UPLOADED, a ``downloadUrl`` (or ``download_url``).
        """
        if not self.configured or not meeting_id or str(meeting_id).startswith("mock-"):
            return []

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    self._recordings_url(),
                    headers=self._headers(),
                    params={"meeting_id": meeting_id},
                )
                if response.status_code >= 400:
                    logger.error(
                        "RealtimeKit list_recordings failed: %s %s",
                        response.status_code,
                        response.text,
                    )
                    return []
                data = response.json()
        except httpx.HTTPError:
            logger.exception("RealtimeKit list_recordings failed")
            return []

        body = data.get("data") if isinstance(data.get("data"), (list, dict)) else data
        if isinstance(body, dict):
            items = body.get("recordings") or body.get("items") or []
        else:
            items = body
        return [item for item in items if isinstance(item, dict)]

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
            url = item.get("downloadUrl") or item.get("download_url")
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
