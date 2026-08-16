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
            "record_on_start": False,
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
