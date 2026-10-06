"""R2 backfill for an existing RealtimeKit recording."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.services.realtimekit import RealtimeKitService
from app.services.recording_archive import (
    RecordingArchiveService,
    verify_realtimekit_signature,
)

RECORDING_ID = "fff4d97c-b29d-4a88-8fb6-0d46e13ee11c"
client = TestClient(app)


class _Missing(Exception):
    def __init__(self) -> None:
        super().__init__("missing")
        self.response = {"Error": {"Code": "404"}}


class FakeS3:
    def __init__(self, *, size_override: int | None = None) -> None:
        self.objects: dict[tuple[str, str], dict] = {}
        self.uploads: list[dict] = []
        self.deleted: list[str] = []
        self.size_override = size_override

    def head_object(self, Bucket: str, Key: str) -> dict:
        item = self.objects.get((Bucket, Key))
        if item is None:
            raise _Missing()
        return {"ContentLength": item["size"]}

    def upload_file(self, Filename: str, Bucket: str, Key: str, ExtraArgs: dict | None = None) -> None:
        extra = ExtraArgs or {}
        assert "ACL" not in extra
        size = self.size_override if self.size_override is not None else Path(Filename).stat().st_size
        self.objects[(Bucket, Key)] = {"size": size, "extra": extra}
        self.uploads.append({"key": Key, "extra": extra})

    def delete_object(self, Bucket: str, Key: str) -> None:
        self.objects.pop((Bucket, Key), None)
        self.deleted.append(Key)


class FakeKit:
    def __init__(self, recording: dict | None) -> None:
        self.recording = recording

    def get_recording(self, recording_id: str) -> dict | None:
        return self.recording

    def find_recording_in_list(self, recording_id: str) -> dict | None:
        return None

    def recording_meeting_id(self, recording: dict) -> str | None:
        meeting = recording.get("meeting") or {}
        return meeting.get("id")

    recording_download_url = staticmethod(RealtimeKitService.recording_download_url)
    recording_title = staticmethod(RealtimeKitService.recording_title)


def _settings(**overrides) -> Settings:
    base = {
        "database_url": "postgresql://u:p@localhost:5432/db",
        "secret_key": "x" * 32,
        "cloudflare_account_id": "acct123",
        "cloudflare_api_token": "token123",
        "realtimekit_app_id": "app123",
        "r2_access_key_id": "r2-key",
        "r2_secret_access_key": "r2-secret",
        "r2_bucket": "analytic-sages-classroom",
        "r2_recording_prefix": "live-sessions/",
        "realtimekit_webhook_secret": "hook-secret",
    }
    base.update(overrides)
    return Settings(**base)


def _recording(**overrides) -> dict:
    future = (datetime.now(timezone.utc) + timedelta(days=6)).isoformat()
    body = {
        "id": RECORDING_ID,
        "status": "UPLOADED",
        "download_url": "https://recordings.example/file.mp4",
        "download_url_expiry": future,
        "started_at": "2026-10-05T17:56:14Z",
        "session_id": "3335c1f7-7c9b-4f6e-99a4-700b9a3384fe",
        "meeting": {
            "id": "bbb5d80c-98ad-4b94-acab-1b49c00c49da",
            "title": "Programme orientation & systems thinking",
        },
    }
    body.update(overrides)
    return body


def _service(recording: dict | None, s3: FakeS3 | None = None, **settings) -> RecordingArchiveService:
    store = s3 or FakeS3()

    def download(url: str, dest: Path) -> int:
        assert url.startswith("https://")
        dest.write_bytes(b"video-bytes")
        return dest.stat().st_size

    return RecordingArchiveService(
        _settings(**settings),
        realtimekit=FakeKit(recording),
        s3_client=store,
        downloader=download,
    )


def test_archives_completed_recording_and_verifies_size():
    store = FakeS3()
    result = _service(_recording(), store).backfill(RECORDING_ID)
    assert result.success is True
    assert result.outcome == "archived"
    assert result.bucket == "analytic-sages-classroom"
    assert result.object_key == f"live-sessions/{RECORDING_ID}.mp4"
    assert result.size_bytes == len(b"video-bytes")
    stored = store.uploads[0]["extra"]
    assert stored["ContentType"] == "video/mp4"
    assert stored["Metadata"]["recording-id"] == RECORDING_ID
    assert stored["Metadata"]["meeting-id"] == "bbb5d80c-98ad-4b94-acab-1b49c00c49da"
    assert "ACL" not in stored


def test_existing_object_is_not_uploaded_again():
    store = FakeS3()
    key = f"live-sessions/{RECORDING_ID}.mp4"
    store.objects[("analytic-sages-classroom", key)] = {"size": 42}
    result = _service(_recording(), store).backfill(RECORDING_ID)
    assert result.success is True
    assert result.outcome == "already_present"
    assert result.size_bytes == 42
    assert store.uploads == []


def test_expired_download_is_a_failure():
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    store = FakeS3()
    result = _service(_recording(download_url_expiry=past), store).backfill(RECORDING_ID)
    assert result.success is False
    assert result.outcome == "expired"
    assert store.uploads == []


def test_missing_recording_is_a_failure():
    result = _service(None).backfill(RECORDING_ID)
    assert result.success is False
    assert result.outcome == "unavailable"


def test_incomplete_status_is_not_archived():
    store = FakeS3()
    result = _service(_recording(status="RECORDING"), store).backfill(RECORDING_ID)
    assert result.success is False
    assert result.outcome == "not_ready"
    assert store.uploads == []


def test_download_size_must_match_provider_metadata():
    store = FakeS3()
    result = _service(_recording(file_size=999), store).backfill(RECORDING_ID)
    assert result.success is False
    assert result.outcome == "failed"
    assert store.uploads == []


def test_size_mismatch_is_not_success():
    store = FakeS3(size_override=1)
    result = _service(_recording(), store).backfill(RECORDING_ID)
    assert result.success is False
    assert result.outcome == "failed"
    assert store.deleted == [f"live-sessions/{RECORDING_ID}.mp4"]


def test_unconfigured_r2_is_not_success():
    result = _service(
        _recording(),
        r2_access_key_id=None,
        r2_secret_access_key=None,
    ).backfill(RECORDING_ID)
    assert result.success is False
    assert result.outcome == "not_configured"


def test_webhook_uploaded_uses_backfill():
    store = FakeS3()
    service = _service(_recording(), store)
    result = service.handle_webhook(
        {"event": "recording.statusUpdate", "recording": {"id": RECORDING_ID, "status": "UPLOADED"}}
    )
    assert result.success is True
    assert result.outcome == "archived"


def test_webhook_in_progress_does_not_upload():
    store = FakeS3()
    service = _service(_recording(), store)
    result = service.handle_webhook(
        {"event": "recording.statusUpdate", "recording": {"id": RECORDING_ID, "status": "RECORDING"}}
    )
    assert result.success is False
    assert result.outcome == "not_ready"
    assert store.uploads == []


def test_webhook_signature_and_unsigned_rejection():
    body = json.dumps({"event": "recording.statusUpdate"}).encode()
    signature = hmac.new(b"hook-secret", body, hashlib.sha256).hexdigest()
    assert verify_realtimekit_signature("hook-secret", body, {"dyte-signature": signature})
    assert not verify_realtimekit_signature("hook-secret", body, {"dyte-signature": "nope"})
    response = client.post("/api/v1/webhooks/realtimekit", content=body, headers={"content-type": "application/json"})
    assert response.status_code == 401
