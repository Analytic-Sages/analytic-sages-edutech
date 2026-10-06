"""Copy a finished RealtimeKit recording into the private Cloudflare R2 bucket.

The temporary RealtimeKit download URL is fetched only on the server, streamed to a
temp file, and uploaded under ``live-sessions/{recording_id}.mp4``. Success is
reported only after the object is confirmed to exist with the same byte size.
An expired or missing download is a failure — nothing is invented.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import httpx

from app.core.config import Settings
from app.services.realtimekit import RealtimeKitError, RealtimeKitService

logger = logging.getLogger(__name__)

READY_STATUSES = {"UPLOADED", "COMPLETED"}
MAX_RECORDING_BYTES = 8 * 1024 * 1024 * 1024
DOWNLOAD_ATTEMPTS = 3
_RECORDING_ID = re.compile(r"^[A-Za-z0-9_-]{3,120}$")
_SIGNATURE_HEADERS = ("dyte-signature", "x-realtimekit-signature")


class RecordingArchiveError(Exception):
    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


@dataclass
class ArchiveOutcome:
    recording_id: str
    success: bool
    outcome: str
    detail: str
    bucket: str | None = None
    object_key: str | None = None
    size_bytes: int | None = None
    provider_status: str | None = None
    retryable: bool = False


def verify_realtimekit_signature(secret: str, body: bytes, headers: dict[str, str]) -> bool:
    """Constant-time check of the RealtimeKit HMAC-SHA256 hex signature."""
    if not secret:
        return False
    provided = ""
    lowered = {key.lower(): value for key, value in headers.items()}
    for name in _SIGNATURE_HEADERS:
        if lowered.get(name):
            provided = lowered[name].strip()
            break
    if provided.lower().startswith("sha256="):
        provided = provided.split("=", 1)[1].strip()
    if not provided:
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided)


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _ascii(value: str, limit: int = 180) -> str:
    cleaned = "".join(ch if 32 <= ord(ch) < 127 else " " for ch in value)
    return " ".join(cleaned.split())[:limit]


def _positive_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _object_missing(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    if not isinstance(response, dict):
        return False
    code = str((response.get("Error") or {}).get("Code", ""))
    return code in {"404", "NoSuchKey", "NotFound"}


class RecordingArchiveService:
    def __init__(
        self,
        settings: Settings,
        realtimekit: RealtimeKitService | None = None,
        s3_client: Any | None = None,
        downloader: Callable[[str, Path], int] | None = None,
    ) -> None:
        self.settings = settings
        self.realtimekit = realtimekit or RealtimeKitService(settings)
        self._s3 = s3_client
        self._downloader = downloader or self._download

    def object_key(self, recording_id: str) -> str:
        if not _RECORDING_ID.fullmatch(recording_id):
            raise RecordingArchiveError("Recording id is not a safe object name")
        prefix = self.settings.r2_recording_prefix_normalized
        return f"{prefix}/{recording_id}.mp4"

    def backfill(self, recording_id: str) -> ArchiveOutcome:
        recording_id = recording_id.strip()
        bucket = self.settings.r2_bucket.strip()
        try:
            key = self.object_key(recording_id)
        except RecordingArchiveError as exc:
            return self._fail(recording_id, "failed", str(exc))

        if not self.settings.r2_configured:
            logger.error("Recording archive skipped recording_id=%s reason=r2_not_configured", recording_id)
            return self._fail(
                recording_id,
                "not_configured",
                "R2 is not configured. Set R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, and the account id or R2_ENDPOINT_URL.",
                bucket=bucket,
                object_key=key,
            )

        try:
            existing = self._head(bucket, key)
        except RecordingArchiveError as exc:
            return self._fail(
                recording_id,
                "failed",
                str(exc),
                bucket=bucket,
                object_key=key,
                retryable=exc.retryable,
            )
        if existing is not None and existing > 0:
            logger.info(
                "Recording archive already present recording_id=%s key=%s size=%s",
                recording_id,
                key,
                existing,
            )
            return ArchiveOutcome(
                recording_id=recording_id,
                success=True,
                outcome="already_present",
                detail=f"Recording is already in R2 ({existing} bytes). No second upload was made.",
                bucket=bucket,
                object_key=key,
                size_bytes=existing,
            )

        try:
            recording = self._load_recording(recording_id)
        except RealtimeKitError as exc:
            logger.error(
                "Recording archive metadata failed recording_id=%s status=%s",
                recording_id,
                exc.status_code,
            )
            return self._fail(
                recording_id,
                "unavailable",
                "RealtimeKit could not return this recording.",
                bucket=bucket,
                object_key=key,
                retryable=exc.status_code >= 500,
            )

        if recording is None:
            logger.info("Recording archive unavailable recording_id=%s", recording_id)
            return self._fail(
                recording_id,
                "unavailable",
                "RealtimeKit has no recording with this id.",
                bucket=bucket,
                object_key=key,
            )

        provider_status = str(recording.get("status") or "").upper() or None
        download_url = self.realtimekit.recording_download_url(recording)
        expires_at = _parse_dt(
            recording.get("download_url_expiry")
            or recording.get("downloadUrlExpiry")
            or recording.get("expires_at")
            or recording.get("expiresAt")
        )
        if provider_status not in READY_STATUSES:
            logger.info(
                "Recording archive not ready recording_id=%s status=%s",
                recording_id,
                provider_status,
            )
            return self._fail(
                recording_id,
                "not_ready",
                f"Recording status is {provider_status or 'unknown'}. It was not uploaded.",
                bucket=bucket,
                object_key=key,
                provider_status=provider_status,
            )
        if expires_at is not None and expires_at <= datetime.now(timezone.utc):
            logger.info("Recording archive expired recording_id=%s", recording_id)
            return self._fail(
                recording_id,
                "expired",
                "The RealtimeKit download link has expired. The recording was not archived.",
                bucket=bucket,
                object_key=key,
                provider_status=provider_status,
            )
        if not download_url or not download_url.startswith("https://"):
            logger.info("Recording archive missing download recording_id=%s", recording_id)
            return self._fail(
                recording_id,
                "unavailable",
                "The recording is marked complete but has no usable download URL.",
                bucket=bucket,
                object_key=key,
                provider_status=provider_status,
            )

        metadata = self._metadata(recording_id, recording, provider_status)
        expected_size = _positive_int(recording.get("file_size") or recording.get("fileSize"))
        try:
            size = self._transfer(download_url, bucket, key, metadata, expected_size)
        except RecordingArchiveError as exc:
            logger.error(
                "Recording archive transfer failed recording_id=%s retryable=%s",
                recording_id,
                exc.retryable,
            )
            return self._fail(
                recording_id,
                "failed",
                str(exc),
                bucket=bucket,
                object_key=key,
                provider_status=provider_status,
                retryable=exc.retryable,
            )

        logger.info(
            "Recording archive stored recording_id=%s key=%s size=%s",
            recording_id,
            key,
            size,
        )
        return ArchiveOutcome(
            recording_id=recording_id,
            success=True,
            outcome="archived",
            detail=f"Recording archived to R2 ({size} bytes).",
            bucket=bucket,
            object_key=key,
            size_bytes=size,
            provider_status=provider_status,
        )

    def handle_webhook(self, payload: dict[str, Any]) -> ArchiveOutcome:
        event = str(payload.get("event") or payload.get("type") or "")
        recording = payload.get("recording") if isinstance(payload.get("recording"), dict) else None
        data = payload.get("data") if isinstance(payload.get("data"), dict) else None
        source = recording or data or payload
        recording_id = str(
            source.get("id")
            or source.get("recording_id")
            or source.get("recordingId")
            or ""
        ).strip()
        status = str(source.get("status") or source.get("recordingStatus") or "").upper()
        logger.info(
            "RealtimeKit recording webhook event=%s recording_id=%s status=%s",
            event or "unknown",
            recording_id or "missing",
            status or "missing",
        )
        if event and "recording" not in event.lower():
            return ArchiveOutcome(
                recording_id=recording_id or "unknown",
                success=False,
                outcome="ignored",
                detail="Event is not a recording status update.",
            )
        if not recording_id:
            return self._fail("unknown", "failed", "Recording status webhook did not include a recording id.")
        if status and status not in READY_STATUSES:
            return self._fail(
                recording_id,
                "not_ready",
                f"Recording status is {status}. Upload starts only after it is uploaded.",
                provider_status=status,
            )
        return self.backfill(recording_id)

    def _load_recording(self, recording_id: str) -> dict[str, Any] | None:
        detail = self.realtimekit.get_recording(recording_id)
        listed = None
        try:
            listed = self.realtimekit.find_recording_in_list(recording_id)
        except RealtimeKitError:
            listed = None
        if detail is None and listed is None:
            return None
        merged: dict[str, Any] = dict(listed or {})
        for key, value in (detail or {}).items():
            if value not in (None, "", [], {}):
                merged[key] = value
        if not self.realtimekit.recording_download_url(merged):
            fallback = self.realtimekit.recording_download_url(listed or {}) or self.realtimekit.recording_download_url(
                detail or {}
            )
            if fallback:
                merged["download_url"] = fallback
        return merged

    def _transfer(
        self,
        url: str,
        bucket: str,
        key: str,
        metadata: dict[str, str],
        expected_size: int | None,
    ) -> int:
        with tempfile.TemporaryDirectory(prefix="rtk-archive-") as directory:
            path = Path(directory) / "recording.mp4"
            size = self._downloader(url, path)
            if size <= 0 or not path.is_file():
                raise RecordingArchiveError("Download was empty", retryable=True)
            if expected_size is not None and size != expected_size:
                raise RecordingArchiveError(
                    "Downloaded recording size does not match RealtimeKit metadata.",
                    retryable=True,
                )
            client = self._client()
            try:
                client.upload_file(
                    str(path),
                    bucket,
                    key,
                    ExtraArgs={"ContentType": "video/mp4", "Metadata": metadata},
                )
            except Exception as exc:
                logger.exception("R2 upload failed key=%s", key)
                raise RecordingArchiveError("Upload to R2 failed.", retryable=True) from exc
            confirmed = self._head(bucket, key)
            if confirmed != size:
                self._delete_quiet(client, bucket, key)
                raise RecordingArchiveError(
                    "R2 object size did not match the downloaded recording.",
                    retryable=True,
                )
            return confirmed

    def _download(self, url: str, dest: Path) -> int:
        timeout = httpx.Timeout(connect=20.0, read=600.0, write=60.0, pool=20.0)
        last_error = "Download failed."
        retryable = True
        for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
            try:
                written = 0
                with httpx.stream("GET", url, timeout=timeout, follow_redirects=True) as response:
                    if response.status_code in {401, 403, 404, 410}:
                        retryable = False
                        last_error = "RealtimeKit refused the recording download."
                        break
                    if response.status_code >= 400:
                        last_error = "RealtimeKit download failed."
                        raise RecordingArchiveError(last_error, retryable=True)
                    with dest.open("wb") as handle:
                        for chunk in response.iter_bytes(1024 * 1024):
                            written += len(chunk)
                            if written > MAX_RECORDING_BYTES:
                                raise RecordingArchiveError(
                                    "Recording is larger than the archive limit.",
                                    retryable=False,
                                )
                            handle.write(chunk)
                if written <= 0:
                    raise RecordingArchiveError("Download was empty", retryable=True)
                return written
            except RecordingArchiveError as exc:
                last_error = str(exc)
                retryable = exc.retryable
                if not exc.retryable:
                    break
            except httpx.HTTPError:
                last_error = "Recording download timed out or was interrupted."
                retryable = True
            if attempt < DOWNLOAD_ATTEMPTS and retryable:
                time.sleep(attempt)
        raise RecordingArchiveError(last_error, retryable=retryable)

    def _head(self, bucket: str, key: str) -> int | None:
        try:
            head = self._client().head_object(Bucket=bucket, Key=key)
        except Exception as exc:
            if _object_missing(exc):
                return None
            logger.exception("R2 head failed key=%s", key)
            raise RecordingArchiveError("Could not verify the R2 object.", retryable=True) from exc
        return int(head.get("ContentLength") or 0)

    def _client(self) -> Any:
        if self._s3 is not None:
            return self._s3
        import boto3
        from botocore.config import Config

        endpoint = self.settings.resolved_r2_endpoint
        self._s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=self.settings.r2_access_key_id,
            aws_secret_access_key=self.settings.r2_secret_access_key,
            region_name="auto",
            config=Config(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "standard"},
                connect_timeout=30,
                read_timeout=120,
            ),
        )
        return self._s3

    @staticmethod
    def _delete_quiet(client: Any, bucket: str, key: str) -> None:
        try:
            client.delete_object(Bucket=bucket, Key=key)
        except Exception:
            logger.exception("Could not remove mismatched R2 object key=%s", key)

    def _metadata(
        self, recording_id: str, recording: dict[str, Any], provider_status: str | None
    ) -> dict[str, str]:
        meeting_id = self.realtimekit.recording_meeting_id(recording) or ""
        title = self.realtimekit.recording_title(recording) or ""
        started = recording.get("started_at") or recording.get("startedAt") or ""
        session_id = recording.get("session_id") or recording.get("sessionId") or ""
        meta = {
            "recording-id": recording_id,
            "provider-status": provider_status or "",
            "meeting-id": _ascii(str(meeting_id), 80),
            "session-id": _ascii(str(session_id), 80),
            "title": _ascii(title),
            "started-at": _ascii(str(started), 40),
        }
        return {key: value for key, value in meta.items() if value}

    @staticmethod
    def _fail(
        recording_id: str,
        outcome: str,
        detail: str,
        *,
        bucket: str | None = None,
        object_key: str | None = None,
        provider_status: str | None = None,
        retryable: bool = False,
    ) -> ArchiveOutcome:
        return ArchiveOutcome(
            recording_id=recording_id,
            success=False,
            outcome=outcome,
            detail=detail,
            bucket=bucket,
            object_key=object_key,
            provider_status=provider_status,
            retryable=retryable,
        )
