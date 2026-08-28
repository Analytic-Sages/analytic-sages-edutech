from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.models.opportunity import OpportunitySource
from app.services.opportunity_sources.base import (
    FETCH_TIMEOUT_SECONDS,
    MAX_BODY_BYTES,
    MAX_ITEMS_PER_SYNC,
    USER_AGENT,
    RawOpportunity,
)
from app.services.opportunity_sources.rss import strip_html
from app.services.opportunity_urls import hostname_of, validate_http_url

logger = logging.getLogger(__name__)
BOARD_TOKEN_RE = re.compile(r"^[a-zA-Z0-9_-]{2,80}$")
GREENHOUSE_HOST = "boards-api.greenhouse.io"
WHITESPACE_RE = re.compile(r"\s+")


def _collapse(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value).strip()


def _parse_datetime(value: object) -> datetime | None:
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


def parse_jobs(payload: dict[str, Any], source: OpportunitySource) -> list[RawOpportunity]:
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        return []
    results: list[RawOpportunity] = []
    for job in jobs[:MAX_ITEMS_PER_SYNC]:
        if not isinstance(job, dict):
            continue
        title = _collapse(str(job.get("title") or ""))[:255]
        job_id = str(job.get("id") or "").strip()
        url = str(job.get("absolute_url") or "").strip()
        if not title or not job_id:
            continue
        location = ""
        loc = job.get("location")
        if isinstance(loc, dict):
            location = _collapse(str(loc.get("name") or ""))[:255]
        content = _collapse(strip_html(str(job.get("content") or "")))[:20000]
        org = _collapse(str(job.get("company_name") or source.name))[:255]
        results.append(
            RawOpportunity(
                external_id=job_id[:255],
                title=title,
                organization_name=org or source.name,
                description=content,
                location=location,
                application_url=url,
                source_url=url or None,
                posted_at=_parse_datetime(job.get("updated_at") or job.get("created_at") or job.get("first_published")),
                deadline=_parse_datetime(job.get("application_deadline")),
                raw_data={"id": job_id, "absolute_url": url},
            )
        )
    return results


def fetch_board(board_token: str) -> dict[str, Any]:
    if not BOARD_TOKEN_RE.fullmatch(board_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Greenhouse board_token must be alphanumeric",
        )
    url = f"https://{GREENHOUSE_HOST}/v1/boards/{board_token}/jobs?content=true"
    validate_http_url(url, "greenhouse_url")
    try:
        with httpx.Client(
            timeout=FETCH_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        ) as client:
            response = client.get(url)
            final_host = hostname_of(str(response.url))
            if final_host != GREENHOUSE_HOST:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Greenhouse request redirected away from the public board API",
                )
            response.raise_for_status()
            if len(response.content) > MAX_BODY_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Greenhouse payload is too large to ingest",
                )
            payload = response.json()
            if not isinstance(payload, dict):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Greenhouse returned an unexpected payload",
                )
            return payload
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        logger.warning("Greenhouse fetch failed for %s: %s", board_token, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch Greenhouse board",
        ) from exc


class GreenhouseConnector:
    connector_type = "greenhouse"

    def fetch(self, source: OpportunitySource) -> list[RawOpportunity]:
        board_token = str((source.config or {}).get("board_token") or "").strip()
        if not board_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Greenhouse sources require config.board_token",
            )
        return parse_jobs(fetch_board(board_token), source)
