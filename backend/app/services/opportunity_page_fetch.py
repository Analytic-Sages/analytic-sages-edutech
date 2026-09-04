"""Fetch public opportunity pages safely (SSRF-aware) for grounding AI extraction."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from html import unescape
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, status

from app.services.opportunity_sources.base import FETCH_TIMEOUT_SECONDS, MAX_BODY_BYTES, USER_AGENT
from app.services.opportunity_urls import (
    hostname_of,
    is_aggregator_url,
    is_shortened_url,
    validate_http_url,
)

logger = logging.getLogger(__name__)

SCRIPT_STYLE_RE = re.compile(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class PageFetchResult:
    url: str
    final_url: str
    text: str
    content_type: str
    bytes_read: int


def html_to_text(html: str, *, max_chars: int = 12_000) -> str:
    cleaned = SCRIPT_STYLE_RE.sub(" ", html)
    cleaned = TAG_RE.sub(" ", cleaned)
    cleaned = unescape(cleaned)
    cleaned = WS_RE.sub(" ", cleaned).strip()
    if len(cleaned) > max_chars:
        return cleaned[:max_chars]
    return cleaned


def fetch_public_page(
    url: str,
    *,
    max_bytes: int = MAX_BODY_BYTES,
    max_text_chars: int = 12_000,
    allow_aggregators: bool = False,
) -> PageFetchResult:
    """Fetch an official opportunity page and return plain text.

    Rejects private hosts, short links, and (by default) aggregator boards.
    Re-validates the final redirect host.
    """
    cleaned = validate_http_url(url, "page_url")
    if not cleaned.lower().startswith("https://"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="page_url must use https",
        )
    if is_shortened_url(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shortened URLs cannot be fetched for grounding",
        )
    if not allow_aggregators and is_aggregator_url(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aggregator URLs cannot be fetched for grounding",
        )

    try:
        with httpx.Client(
            timeout=FETCH_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5"},
        ) as client:
            response = client.get(cleaned)
            final_url = str(response.url)
            # Re-validate landing host (SSRF / private redirect).
            validate_http_url(final_url, "page_url")
            final_host = hostname_of(final_url)
            if not final_host:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="page_url host is not allowed",
                )
            if is_shortened_url(final_url):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Shortened redirect targets are not allowed",
                )
            if not allow_aggregators and is_aggregator_url(final_url):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Aggregator redirect targets are not allowed",
                )
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Could not fetch opportunity page ({response.status_code})",
                )
            body = response.content
            if len(body) > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Opportunity page is too large to process",
                )
            content_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
            raw = body.decode(response.encoding or "utf-8", errors="replace")
            if "html" in content_type or raw.lstrip().lower().startswith("<!doctype") or "<html" in raw[:500].lower():
                text = html_to_text(raw, max_chars=max_text_chars)
            else:
                text = WS_RE.sub(" ", raw).strip()[:max_text_chars]
            if len(text) < 40:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Opportunity page returned too little text to extract",
                )
            return PageFetchResult(
                url=cleaned,
                final_url=final_url[:500],
                text=text,
                content_type=content_type or "text/plain",
                bytes_read=len(body),
            )
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        logger.warning("Public page fetch failed for %s: %s", urlparse(cleaned).hostname, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch opportunity page",
        ) from exc
