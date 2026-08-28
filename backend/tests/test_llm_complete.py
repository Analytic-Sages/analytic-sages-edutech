from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.llm_complete import complete_json, llm_configured


def _settings(**overrides):
    values = {
        "openai_api_key": None,
        "openai_model": "gpt-4.1-mini",
        "gemini_api_key": None,
        "gemini_model": "gemini-2.0-flash",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _response(url: str, status_code: int, payload: dict):
    resp = MagicMock()
    resp.url = url
    resp.status_code = status_code
    resp.json.return_value = payload
    return resp


def _client(post):
    mock = MagicMock()
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = False
    mock.post.side_effect = post
    return mock


def test_llm_configured_with_either_key():
    assert llm_configured(_settings()) is False
    assert llm_configured(_settings(openai_api_key="sk-test")) is True
    assert llm_configured(_settings(gemini_api_key="gemini-test")) is True


def test_complete_json_requires_a_key():
    with pytest.raises(HTTPException) as exc:
        complete_json(_settings(), instructions="sys", user_content="user")
    assert exc.value.status_code == 503


def test_complete_json_uses_openai_first():
    def post(url, **kwargs):
        assert "api.openai.com" in url
        return _response(
            url,
            200,
            {"choices": [{"message": {"content": '{"hello": "openai"}'}}]},
        )

    with patch("app.services.llm_complete.httpx.Client", return_value=_client(post)):
        parsed, grounded, provider = complete_json(
            _settings(openai_api_key="sk-test", gemini_api_key="gemini-test"),
            instructions="sys",
            user_content="user",
            with_search=False,
        )
    assert provider == "openai"
    assert parsed == {"hello": "openai"}
    assert grounded is False


def test_complete_json_falls_back_to_gemini_when_openai_fails():
    def post(url, **kwargs):
        if "api.openai.com" in url:
            return _response(url, 401, {"error": "unauthorized"})
        return _response(
            url,
            200,
            {"candidates": [{"content": {"parts": [{"text": '{"hello": "gemini"}'}]}}]},
        )

    with patch("app.services.llm_complete.httpx.Client", return_value=_client(post)):
        parsed, grounded, provider = complete_json(
            _settings(openai_api_key="sk-test", gemini_api_key="gemini-test"),
            instructions="sys",
            user_content="user",
            with_search=False,
        )
    assert provider == "gemini"
    assert parsed == {"hello": "gemini"}
    assert grounded is False


def test_complete_json_uses_gemini_when_openai_missing():
    def post(url, **kwargs):
        assert "generativelanguage.googleapis.com" in url
        return _response(
            url,
            200,
            {"candidates": [{"content": {"parts": [{"text": '{"hello": "gemini-only"}'}]}}]},
        )

    with patch("app.services.llm_complete.httpx.Client", return_value=_client(post)):
        parsed, grounded, provider = complete_json(
            _settings(gemini_api_key="gemini-test"),
            instructions="sys",
            user_content="user",
            with_search=False,
        )
    assert provider == "gemini"
    assert parsed == {"hello": "gemini-only"}
    assert grounded is False
