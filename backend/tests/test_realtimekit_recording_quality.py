from __future__ import annotations

from app.core.config import get_settings
from app.services import realtimekit as realtimekit_module
from app.services.realtimekit import RealtimeKitService


class FakeResponse:
    status_code = 200
    text = ""

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"success": True, "data": {"id": "meeting-123"}}


class FakeClient:
    def __init__(self, *, timeout: float) -> None:
        self.timeout = timeout
        self.calls: list[dict] = []

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, *args) -> None:
        return None

    def post(self, url: str, *, headers: dict, json: dict) -> FakeResponse:
        self.calls.append({"url": url, "headers": headers, "json": json})
        return FakeResponse()


def configured_settings(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "cloudflare_account_id", "account-test")
    monkeypatch.setattr(settings, "cloudflare_api_token", "token-test")
    monkeypatch.setattr(settings, "realtimekit_app_id", "app-test")
    monkeypatch.setattr(settings, "realtimekit_record_on_start", True)
    monkeypatch.setattr(settings, "realtimekit_recording_video_width", 1920)
    monkeypatch.setattr(settings, "realtimekit_recording_video_height", 1080)
    monkeypatch.setattr(settings, "realtimekit_recording_video_codec", "H264")
    return settings


def test_create_meeting_requests_high_quality_recording(monkeypatch) -> None:
    settings = configured_settings(monkeypatch)
    fake_client = FakeClient(timeout=30.0)
    monkeypatch.setattr(realtimekit_module.httpx, "Client", lambda **kwargs: fake_client)

    meeting_id = RealtimeKitService(settings).create_meeting(title="SQL Workshop")

    assert meeting_id == "meeting-123"
    assert len(fake_client.calls) == 1
    call = fake_client.calls[0]
    assert call["url"].endswith("/meetings")
    assert call["json"]["record_on_start"] is True
    assert call["json"]["recording_config"]["video_config"] == {
        "codec": "H264",
        "width": 1920,
        "height": 1080,
    }
    assert call["json"]["recording_config"]["audio_config"] == {
        "codec": "AAC",
        "channel": "stereo",
    }


def test_explicit_recording_uses_documented_recordings_endpoint(monkeypatch) -> None:
    settings = configured_settings(monkeypatch)
    fake_client = FakeClient(timeout=30.0)
    monkeypatch.setattr(realtimekit_module.httpx, "Client", lambda **kwargs: fake_client)

    assert RealtimeKitService(settings).start_recording(meeting_id="meeting-123") is True

    assert len(fake_client.calls) == 1
    call = fake_client.calls[0]
    assert call["url"].endswith("/realtime/kit/app-test/recordings")
    assert call["json"]["meeting_id"] == "meeting-123"
    assert call["json"]["video_config"] == {
        "codec": "H264",
        "width": 1920,
        "height": 1080,
    }
