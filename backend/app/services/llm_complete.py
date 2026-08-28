from __future__ import annotations

import json
import logging
import re

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings
from app.services.opportunity_urls import hostname_of, validate_http_url

logger = logging.getLogger(__name__)
OPENAI_HOST = "api.openai.com"
GEMINI_HOST = "generativelanguage.googleapis.com"
MODEL_NAME_RE = re.compile(r"^[a-zA-Z0-9._-]+$")


def llm_configured(settings: Settings) -> bool:
    return bool((settings.openai_api_key or "").strip() or (settings.gemini_api_key or "").strip())


def complete_json(
    settings: Settings,
    *,
    instructions: str,
    user_content: str,
    with_search: bool = False,
) -> tuple[dict, bool, str]:
    """Try OpenAI first, then Gemini. Returns (payload, grounded, provider)."""
    errors: list[str] = []
    openai_key = (settings.openai_api_key or "").strip()
    gemini_key = (settings.gemini_api_key or "").strip()
    if openai_key:
        try:
            parsed, grounded = _openai_json(
                openai_key,
                settings.openai_model,
                instructions,
                user_content,
                with_search=with_search,
            )
            if parsed is not None:
                return parsed, grounded, "openai"
            errors.append("openai returned no JSON")
        except HTTPException as exc:
            if exc.status_code not in {502, 503}:
                raise
            errors.append(str(exc.detail))
            logger.info("OpenAI discovery/review failed; trying Gemini if configured")
    if gemini_key:
        try:
            parsed, grounded = _gemini_json(
                gemini_key,
                settings.gemini_model,
                instructions,
                user_content,
                with_search=with_search,
            )
            if parsed is not None:
                return parsed, grounded, "gemini"
            errors.append("gemini returned no JSON")
        except HTTPException as exc:
            if exc.status_code not in {502, 503}:
                raise
            errors.append(str(exc.detail))
    if not openai_key and not gemini_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Language model is not configured. Set OPENAI_API_KEY or GEMINI_API_KEY.",
        )
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Language model request could not complete",
    )


def _openai_json(
    key: str,
    model: str,
    instructions: str,
    user_content: str,
    *,
    with_search: bool,
) -> tuple[dict | None, bool]:
    if with_search:
        parsed = _openai_responses(key, model, instructions, user_content)
        if parsed is not None:
            return parsed, True
    return _openai_chat(key, model, instructions, user_content), False


def _openai_responses(key: str, model: str, instructions: str, user_content: str) -> dict | None:
    url = "https://api.openai.com/v1/responses"
    validate_http_url(url, "openai_url")
    try:
        with httpx.Client(timeout=45.0, follow_redirects=False) as client:
            response = client.post(
                url,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "tools": [{"type": "web_search"}],
                    "instructions": instructions,
                    "input": user_content,
                    "temperature": 0,
                },
            )
            if hostname_of(str(response.url)) != OPENAI_HOST:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OpenAI request left api.openai.com")
            if response.status_code >= 400:
                logger.info("OpenAI responses/web_search unavailable: %s", response.status_code)
                return None
            data = response.json()
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        logger.warning("OpenAI responses failed: %s", exc)
        return None
    text = _openai_output_text(data)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return extract_json_object(text)


def _openai_chat(key: str, model: str, instructions: str, user_content: str) -> dict | None:
    url = "https://api.openai.com/v1/chat/completions"
    validate_http_url(url, "openai_url")
    try:
        with httpx.Client(timeout=45.0, follow_redirects=False) as client:
            response = client.post(
                url,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "response_format": {"type": "json_object"},
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": instructions},
                        {"role": "user", "content": user_content},
                    ],
                },
            )
            if hostname_of(str(response.url)) != OPENAI_HOST:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OpenAI request left api.openai.com")
            if response.status_code >= 400:
                logger.info("OpenAI chat unavailable: %s", response.status_code)
                return None
            data = response.json()
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        logger.warning("OpenAI chat failed: %s", exc)
        return None
    try:
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None


def _gemini_json(
    key: str,
    model: str,
    instructions: str,
    user_content: str,
    *,
    with_search: bool,
) -> tuple[dict | None, bool]:
    safe_model = model if MODEL_NAME_RE.fullmatch(model) else "gemini-2.0-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{safe_model}:generateContent"
    validate_http_url(url, "gemini_url")
    if with_search:
        parsed = _gemini_generate(url, key, instructions, user_content, search=True)
        if parsed is not None:
            return parsed, True
    parsed = _gemini_generate(url, key, instructions, user_content, search=False)
    return parsed, False


def _gemini_generate(
    url: str,
    key: str,
    instructions: str,
    user_content: str,
    *,
    search: bool,
) -> dict | None:
    body: dict = {
        "system_instruction": {"parts": [{"text": instructions}]},
        "contents": [{"role": "user", "parts": [{"text": user_content}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    if search:
        body["tools"] = [{"google_search": {}}]
    try:
        with httpx.Client(timeout=45.0, follow_redirects=False) as client:
            response = client.post(
                url,
                headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                json=body,
            )
            if hostname_of(str(response.url)) != GEMINI_HOST:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Gemini request left generativelanguage.googleapis.com",
                )
            if response.status_code >= 400:
                logger.info("Gemini generateContent unavailable (search=%s): %s", search, response.status_code)
                return None
            data = response.json()
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        logger.warning("Gemini generateContent failed: %s", exc)
        return None
    text = _gemini_text(data)
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = extract_json_object(text)
    return parsed if isinstance(parsed, dict) else None


def _openai_output_text(data: dict) -> str:
    if isinstance(data.get("output_text"), str) and data["output_text"].strip():
        return data["output_text"]
    chunks: list[str] = []
    for item in data.get("output") or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    return "\n".join(chunks).strip()


def _gemini_text(data: dict) -> str:
    try:
        parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError):
        return ""
    chunks: list[str] = []
    for part in parts or []:
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            chunks.append(part["text"])
    return "\n".join(chunks).strip()


def extract_json_object(text: str) -> dict | None:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None
