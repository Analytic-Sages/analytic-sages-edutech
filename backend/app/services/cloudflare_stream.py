"""Cloudflare Stream VOD for self-paced lesson videos.

Reuses the Cloudflare account + API token already configured for RealtimeKit.
When credentials are missing it runs in mock mode so the authoring flow works in
dev without uploads. The lesson stores the returned video UID in ``video_id`` and
``video_provider="cloudflare_stream"``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)

API_BASE = "https://api.cloudflare.com/client/v4"


class CloudflareStreamError(Exception):
    """Raised when Cloudflare Stream API calls fail."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class DirectUpload:
    uid: str
    upload_url: str
    mock: bool = False


@dataclass
class StreamVideo:
    uid: str
    status: str  # pendingupload | downloading | queued | inprogress | ready | error
    duration_seconds: int | None
    thumbnail_url: str | None
    embed_url: str | None
    hls_url: str | None
    mock: bool = False


class CloudflareStreamService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def configured(self) -> bool:
        return self.settings.cloudflare_stream_configured

    @property
    def mode(self) -> str:
        return "live" if self.configured else "mock"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.cloudflare_api_token}",
            "Content-Type": "application/json",
        }

    def _stream_url(self, suffix: str = "") -> str:
        base = f"{API_BASE}/accounts/{self.settings.cloudflare_account_id}/stream"
        return f"{base}{suffix}"

    # ---------- playback URL builders ----------

    def _customer_base(self) -> str:
        code = (self.settings.cloudflare_stream_customer_code or "").strip()
        if not code:
            return ""
        if code.startswith("customer-"):
            return f"https://{code}.cloudflarestream.com"
        return f"https://customer-{code}.cloudflarestream.com"

    def embed_url(self, uid: str) -> str | None:
        base = self._customer_base()
        return f"{base}/{uid}/iframe" if base and uid else None

    def hls_url(self, uid: str) -> str | None:
        base = self._customer_base()
        return f"{base}/{uid}/manifest/video.m3u8" if base and uid else None

    def thumbnail_url(self, uid: str, *, time: str = "1s") -> str | None:
        base = self._customer_base()
        return f"{base}/{uid}/thumbnails/thumbnail.jpg?time={time}" if base and uid else None

    # ---------- API calls ----------

    def create_direct_upload(
        self,
        *,
        max_duration_seconds: int | None = None,
        creator: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> DirectUpload:
        """Return a one-time upload URL the browser POSTs the video file to."""
        if not self.configured:
            mock_uid = f"mock-{creator or 'video'}"
            return DirectUpload(
                uid=mock_uid, upload_url="mock://cloudflare-stream/upload", mock=True
            )

        payload: dict[str, Any] = {
            "maxDurationSeconds": max_duration_seconds
            or self.settings.cloudflare_stream_default_max_duration_seconds,
        }
        if creator:
            payload["creator"] = creator
        if meta:
            payload["meta"] = meta

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self._stream_url("/direct_upload"),
                    headers=self._headers(),
                    json=payload,
                )
                if response.status_code >= 400:
                    logger.error(
                        "Cloudflare Stream direct_upload failed: %s %s",
                        response.status_code,
                        response.text[:400],
                    )
                    raise CloudflareStreamError(
                        "Cloudflare Stream upload link failed",
                        status_code=response.status_code,
                    )
                data = response.json()
        except httpx.HTTPError as exc:
            logger.exception("Cloudflare Stream direct_upload request failed")
            raise CloudflareStreamError("Cloudflare Stream is unreachable") from exc

        result = data.get("result") or {}
        uid = result.get("uid")
        upload_url = result.get("uploadURL")
        if not uid or not upload_url:
            raise CloudflareStreamError(f"Unexpected direct_upload response: {data}")
        return DirectUpload(uid=str(uid), upload_url=str(upload_url))

    def get_video(self, uid: str) -> StreamVideo:
        if not self.configured or uid.startswith("mock-"):
            return StreamVideo(
                uid=uid,
                status="ready",
                duration_seconds=None,
                thumbnail_url=self.thumbnail_url(uid),
                embed_url=self.embed_url(uid),
                hls_url=self.hls_url(uid),
                mock=True,
            )
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(self._stream_url(f"/{uid}"), headers=self._headers())
                if response.status_code >= 400:
                    raise CloudflareStreamError(
                        f"Cloudflare Stream video not found ({response.status_code})",
                        status_code=response.status_code,
                    )
                data = response.json()
        except httpx.HTTPError as exc:
            logger.exception("Cloudflare Stream get_video failed")
            raise CloudflareStreamError("Cloudflare Stream is unreachable") from exc

        result = data.get("result") or {}
        status_obj = result.get("status") or {}
        duration = result.get("duration")
        return StreamVideo(
            uid=str(result.get("uid") or uid),
            status=str(status_obj.get("state") or "unknown"),
            duration_seconds=int(duration) if duration else None,
            thumbnail_url=result.get("thumbnail") or self.thumbnail_url(uid),
            embed_url=self.embed_url(uid),
            hls_url=self.hls_url(uid),
        )

    def delete_video(self, uid: str) -> bool:
        if not self.configured or uid.startswith("mock-"):
            return True
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.delete(self._stream_url(f"/{uid}"), headers=self._headers())
        except httpx.HTTPError as exc:
            logger.exception("Cloudflare Stream delete_video failed")
            raise CloudflareStreamError("Cloudflare Stream is unreachable") from exc
        if response.status_code >= 400 and response.status_code != 404:
            raise CloudflareStreamError(
                f"Cloudflare Stream delete failed ({response.status_code})",
                status_code=response.status_code,
            )
        return True

    def list_videos(self, *, search: str | None = None, limit: int = 50) -> list[StreamVideo]:
        if not self.configured:
            return []
        params: dict[str, Any] = {"limit": limit}
        if search:
            params["search"] = search
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(self._stream_url(), headers=self._headers(), params=params)
                if response.status_code >= 400:
                    raise CloudflareStreamError(
                        f"Cloudflare Stream list failed ({response.status_code})",
                        status_code=response.status_code,
                    )
                data = response.json()
        except httpx.HTTPError as exc:
            logger.exception("Cloudflare Stream list_videos failed")
            raise CloudflareStreamError("Cloudflare Stream is unreachable") from exc

        videos: list[StreamVideo] = []
        for item in data.get("result") or []:
            status_obj = item.get("status") or {}
            duration = item.get("duration")
            uid = str(item.get("uid") or "")
            videos.append(
                StreamVideo(
                    uid=uid,
                    status=str(status_obj.get("state") or "unknown"),
                    duration_seconds=int(duration) if duration else None,
                    thumbnail_url=item.get("thumbnail") or self.thumbnail_url(uid),
                    embed_url=self.embed_url(uid),
                    hls_url=self.hls_url(uid),
                )
            )
        return videos