from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.models.opportunity import OpportunitySource, WorkplaceType
from app.services.opportunity_mission import is_off_mission_title
from app.services.opportunity_sources.base import (
    FETCH_TIMEOUT_SECONDS,
    MAX_ITEMS_PER_SYNC,
    USER_AGENT,
    RawOpportunity,
)
from app.services.opportunity_sources.greenhouse import BOARD_TOKEN_RE, _collapse, _parse_datetime
from app.services.opportunity_sources.rss import strip_html
from app.services.opportunity_urls import hostname_of, validate_http_url

logger = logging.getLogger(__name__)
ASHBY_HOST = "api.ashbyhq.com"
# TRM's public board is ~3MB because Ashby embeds full HTML descriptions.
ASHBY_MAX_BODY_BYTES = 6_000_000


def _workplace(job: dict[str, Any]) -> WorkplaceType | None:
    kind = str(job.get("workplaceType") or "").lower()
    if "hybrid" in kind:
        return WorkplaceType.HYBRID
    if "onsite" in kind or "on-site" in kind:
        return WorkplaceType.ONSITE
    if job.get("isRemote") is True or "remote" in kind:
        return WorkplaceType.REMOTE
    return None


def _rank(job: dict[str, Any]) -> int:
    title = str(job.get("title") or "")
    if is_off_mission_title(title):
        return 2
    haystack = " ".join(
        str(job.get(key) or "") for key in ("title", "department", "team")
    ).lower()
    if any(token in haystack for token in ("data", "intel", "engineer", "research", "analyst", "science", "quant")):
        return 0
    return 1


def parse_jobs(payload: dict[str, Any], source: OpportunitySource) -> list[RawOpportunity]:
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        return []
    listed = [job for job in jobs if isinstance(job, dict) and job.get("isListed", True)]
    listed.sort(key=_rank)
    results: list[RawOpportunity] = []
    for job in listed[:MAX_ITEMS_PER_SYNC]:
        title = _collapse(str(job.get("title") or ""))[:255]
        job_id = str(job.get("id") or "").strip()
        url = str(job.get("jobUrl") or job.get("applyUrl") or "").strip()
        if not title or not job_id or not url:
            continue
        description = _collapse(str(job.get("descriptionPlain") or strip_html(str(job.get("descriptionHtml") or ""))))[
            :20000
        ]
        results.append(
            RawOpportunity(
                external_id=job_id[:255],
                title=title,
                organization_name=source.name,
                description=description,
                location=_collapse(str(job.get("location") or ""))[:255],
                application_url=url,
                source_url=url,
                posted_at=_parse_datetime(job.get("publishedAt")),
                workplace_type=_workplace(job),
                raw_data={"id": job_id, "jobUrl": url, "department": job.get("department")},
            )
        )
    return results


def fetch_board(board_token: str) -> dict[str, Any]:
    if not BOARD_TOKEN_RE.fullmatch(board_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ashby board_token must be alphanumeric",
        )
    url = f"https://{ASHBY_HOST}/posting-api/job-board/{board_token}"
    validate_http_url(url, "ashby_url")
    try:
        with httpx.Client(
            timeout=FETCH_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        ) as client:
            response = client.get(url)
            if hostname_of(str(response.url)) != ASHBY_HOST:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ashby request redirected away from the public job board API",
                )
            response.raise_for_status()
            if len(response.content) > ASHBY_MAX_BODY_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Ashby payload is too large to ingest",
                )
            payload = response.json()
            if not isinstance(payload, dict):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Ashby returned an unexpected payload",
                )
            return payload
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        logger.warning("Ashby fetch failed for %s: %s", board_token, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch Ashby board",
        ) from exc


class AshbyConnector:
    connector_type = "ashby"

    def fetch(self, source: OpportunitySource) -> list[RawOpportunity]:
        board_token = str((source.config or {}).get("board_token") or "").strip()
        if not board_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ashby sources require config.board_token",
            )
        return parse_jobs(fetch_board(board_token), source)
