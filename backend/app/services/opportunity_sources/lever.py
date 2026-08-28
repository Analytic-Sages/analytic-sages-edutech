from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.models.opportunity import OpportunitySource, WorkplaceType
from app.services.opportunity_sources.base import (
    FETCH_TIMEOUT_SECONDS,
    MAX_BODY_BYTES,
    MAX_ITEMS_PER_SYNC,
    USER_AGENT,
    RawOpportunity,
)
from app.services.opportunity_sources.greenhouse import BOARD_TOKEN_RE, _collapse
from app.services.opportunity_sources.rss import strip_html
from app.services.opportunity_urls import hostname_of, validate_http_url

logger = logging.getLogger(__name__)
LEVER_HOST = "api.lever.co"


def _workplace(job: dict[str, Any]) -> WorkplaceType | None:
    kind = str(job.get("workplaceType") or job.get("workType") or "").lower()
    if "hybrid" in kind:
        return WorkplaceType.HYBRID
    if "onsite" in kind or "on-site" in kind:
        return WorkplaceType.ONSITE
    if job.get("isRemote") is True or "remote" in kind:
        return WorkplaceType.REMOTE
    categories = job.get("categories")
    if isinstance(categories, dict):
        location = str(categories.get("location") or "").lower()
        if "remote" in location:
            return WorkplaceType.REMOTE
    return None


def _posted_at(job: dict[str, Any]) -> datetime | None:
    created = job.get("createdAt")
    if isinstance(created, (int, float)):
        seconds = created / 1000 if created > 10_000_000_000 else created
        try:
            return datetime.fromtimestamp(seconds, tz=UTC)
        except (OSError, OverflowError, ValueError):
            return None
    return None


def parse_jobs(payload: list[Any], source: OpportunitySource) -> list[RawOpportunity]:
    results: list[RawOpportunity] = []
    for job in payload[:MAX_ITEMS_PER_SYNC]:
        if not isinstance(job, dict):
            continue
        title = _collapse(str(job.get("text") or job.get("title") or ""))[:255]
        job_id = str(job.get("id") or "").strip()
        url = str(job.get("hostedUrl") or job.get("applyUrl") or "").strip()
        if not title or not job_id or not url:
            continue
        location = ""
        categories = job.get("categories")
        if isinstance(categories, dict):
            location = _collapse(str(categories.get("location") or ""))[:255]
        description = _collapse(
            str(job.get("descriptionPlain") or strip_html(str(job.get("description") or "")))
        )[:20000]
        results.append(
            RawOpportunity(
                external_id=job_id[:255],
                title=title,
                organization_name=source.name,
                description=description,
                location=location,
                application_url=url,
                source_url=url,
                posted_at=_posted_at(job),
                workplace_type=_workplace(job),
                raw_data={"id": job_id, "hostedUrl": url, "categories": categories},
            )
        )
    return results


def fetch_board(board_token: str) -> list[Any]:
    if not BOARD_TOKEN_RE.fullmatch(board_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lever board_token must be alphanumeric",
        )
    url = f"https://{LEVER_HOST}/v0/postings/{board_token}?mode=json"
    validate_http_url(url, "lever_url")
    try:
        with httpx.Client(
            timeout=FETCH_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        ) as client:
            response = client.get(url)
            if hostname_of(str(response.url)) != LEVER_HOST:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Lever request redirected away from the public postings API",
                )
            response.raise_for_status()
            if len(response.content) > MAX_BODY_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Lever payload is too large to ingest",
                )
            payload = response.json()
            if not isinstance(payload, list):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Lever returned an unexpected payload",
                )
            return payload
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        logger.warning("Lever fetch failed for %s: %s", board_token, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch Lever board",
        ) from exc


class LeverConnector:
    connector_type = "lever"

    def fetch(self, source: OpportunitySource) -> list[RawOpportunity]:
        board_token = str((source.config or {}).get("board_token") or "").strip()
        if not board_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lever sources require config.board_token",
            )
        return parse_jobs(fetch_board(board_token), source)
