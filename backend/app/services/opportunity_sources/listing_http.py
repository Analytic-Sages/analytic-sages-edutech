from __future__ import annotations

import logging
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, status

from app.services.opportunity_sources.base import FETCH_TIMEOUT_SECONDS, USER_AGENT
from app.services.opportunity_urls import hostname_of, validate_http_url

logger = logging.getLogger(__name__)


def host_allowed(host: str | None, allowed_hosts: set[str]) -> bool:
    value = (host or "").lower()
    if value in allowed_hosts:
        return True
    return any(value.endswith("." + item) for item in allowed_hosts)


def canonicalize_path_url(
    url: str,
    *,
    allowed_hosts: set[str],
    allowed_paths: set[str],
    canonical: str,
    detail: str,
) -> str:
    cleaned = validate_http_url(url, "listing_url")
    parsed = urlparse(cleaned)
    if not host_allowed(parsed.hostname, allowed_hosts):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    path = (parsed.path or "/").rstrip("/") or "/"
    if path not in allowed_paths:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    return canonical


def parse_iso_datetime(value: object) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def fetch_listing(
    url: str,
    *,
    allowed_hosts: set[str],
    accept: str,
    max_bytes: int,
    failed_detail: str,
    redirected_detail: str,
    too_large_detail: str,
    extra_headers: dict[str, str] | None = None,
) -> httpx.Response:
    validate_http_url(url, "listing_url")
    headers = {"User-Agent": USER_AGENT, "Accept": accept}
    if extra_headers:
        headers.update(extra_headers)
    try:
        with httpx.Client(
            timeout=FETCH_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers=headers,
        ) as client:
            response = client.get(url)
            if not host_allowed(hostname_of(str(response.url)), allowed_hosts):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=redirected_detail,
                )
            if response.status_code >= 400:
                logger.warning("%s (%s)", failed_detail, response.status_code)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=failed_detail,
                )
            if len(response.content) > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=too_large_detail,
                )
            return response
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        logger.warning("%s: %s", failed_detail, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=failed_detail,
        ) from exc
