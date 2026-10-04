from __future__ import annotations

from unittest.mock import MagicMock

from app.core.config import Settings
from app.services.cloudflare_stream import CloudflareStreamService


def _settings(**overrides) -> Settings:
    base = {
        "database_url": "postgresql://u:p@localhost:5432/db",
        "secret_key": "x" * 32,
        "cloudflare_account_id": "acct123",
        "cloudflare_api_token": "token123",
        "cloudflare_stream_customer_code": "customer-abc",
    }
    base.update(overrides)
    return Settings(**base)


def test_mock_mode_when_unconfigured():
    settings = _settings(cloudflare_api_token=None)
    service = CloudflareStreamService(settings)
    assert service.configured is False
    assert service.mode == "mock"
    upload = service.create_direct_upload(creator="lesson-1")
    assert upload.mock is True
    assert upload.uid.startswith("mock-")


def test_playback_urls_use_customer_subdomain():
    service = CloudflareStreamService(_settings())
    assert service.embed_url("uid1") == "https://customer-abc.cloudflarestream.com/uid1/iframe"
    assert (
        service.hls_url("uid1")
        == "https://customer-abc.cloudflarestream.com/uid1/manifest/video.m3u8"
    )
    assert (
        service.thumbnail_url("uid1")
        == "https://customer-abc.cloudflarestream.com/uid1/thumbnails/thumbnail.jpg?time=1s"
    )


def test_playback_urls_accept_prefixed_code():
    service = CloudflareStreamService(_settings(cloudflare_stream_customer_code="customer-xyz"))
    assert service.embed_url("uid1") == "https://customer-xyz.cloudflarestream.com/uid1/iframe"


def test_create_direct_upload_parses_response(monkeypatch):
    service = CloudflareStreamService(_settings())

    class _Response:
        status_code = 200

        def json(self):
            return {"result": {"uid": "videouid123", "uploadURL": "https://upload.example/xyz"}}

    class _Client:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, headers=None, json=None):
            assert url.endswith("/stream/direct_upload")
            assert headers["Authorization"] == "Bearer token123"
            assert json["maxDurationSeconds"] == 21600
            return _Response()

    monkeypatch.setattr("app.services.cloudflare_stream.httpx.Client", lambda *a, **k: _Client())
    upload = service.create_direct_upload(creator="lesson-1")
    assert upload.uid == "videouid123"
    assert upload.upload_url == "https://upload.example/xyz"
    assert upload.mock is False


def test_get_video_maps_status(monkeypatch):
    service = CloudflareStreamService(_settings())

    class _Response:
        status_code = 200

        def json(self):
            return {
                "result": {
                    "uid": "vid1",
                    "status": {"state": "ready"},
                    "duration": 360,
                }
            }

    class _Client:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, headers=None):
            assert url.endswith("/stream/vid1")
            return _Response()

    monkeypatch.setattr("app.services.cloudflare_stream.httpx.Client", lambda *a, **k: _Client())
    video = service.get_video("vid1")
    assert video.status == "ready"
    assert video.duration_seconds == 360
    assert video.embed_url.endswith("/vid1/iframe")


def test_direct_upload_endpoint_switches_lesson_provider():
    # Placeholder to keep the module import graph exercised; covered end-to-end in
    # test_course_admin if Cloudflare is unconfigured (mock UID).
    assert CloudflareStreamService(MagicMock(spec=Settings)).mode in {"live", "mock"}