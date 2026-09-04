from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from fastapi import HTTPException, status

from app.models.opportunity import HackathonEventFormat, OpportunitySource, OpportunityType, WorkplaceType
from app.services.opportunity_sources.base import MAX_BODY_BYTES, RawOpportunity
from app.services.opportunity_sources.listing_http import (
    canonicalize_path_url,
    fetch_listing,
    parse_iso_datetime,
)
from app.services.opportunity_urls import hostname_of

COLOSSEUM_HOSTS = {"colosseum.com", "www.colosseum.com"}
DEFAULT_LISTING_URL = "https://colosseum.com/hackathon/__data.json"
MAX_EVENTS = 30
CLOSED_PHASES = {"concluded", "ended", "closed", "past", "complete", "completed"}
OPEN_PHASES = {"open", "upcoming", "live", "active"}


def _inflate(data: list[Any], item: Any, depth: int = 0) -> Any:
    if depth > 14:
        return None
    if isinstance(item, int):
        if item < 0 or item >= len(data):
            return item
        value = data[item]
        if isinstance(value, dict):
            return {key: _inflate(data, nested, depth + 1) for key, nested in value.items()}
        if isinstance(value, list):
            return [_inflate(data, nested, depth + 1) for nested in value]
        return value
    if isinstance(item, dict):
        return {key: _inflate(data, nested, depth + 1) for key, nested in item.items()}
    if isinstance(item, list):
        return [_inflate(data, nested, depth + 1) for nested in item]
    return item


def _is_open(phase: str, active: object) -> bool:
    key = phase.strip().lower()
    if key in CLOSED_PHASES:
        return False
    if key in OPEN_PHASES:
        return True
    return bool(active)


def _apply_url(url: str) -> str | None:
    cleaned = (url or "").strip()
    if not cleaned:
        return None
    host = hostname_of(cleaned)
    if host not in COLOSSEUM_HOSTS:
        return None
    path = (urlparse(cleaned).path or "/").rstrip("/") or "/"
    return f"https://colosseum.com{path}"


def _title_from_url(url: str, fallback: str) -> str:
    path = (urlparse(url).path or "/").strip("/")
    slug = path.split("/")[-1] if path else ""
    if slug:
        return slug.replace("-", " ").title()[:255]
    return fallback[:255]


def _collect_events(payload: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = payload.get("nodes")
    if not isinstance(nodes, list):
        return []
    events: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict) or node.get("type") != "data":
            continue
        data = node.get("data")
        if not isinstance(data, list) or not data:
            continue
        root = _inflate(data, 0)
        if not isinstance(root, dict):
            continue
        current = root.get("currentEvent")
        if isinstance(current, dict):
            events.append(
                {
                    "name": str(current.get("name") or "").strip(),
                    "event_type": str(current.get("eventType") or "hackathon").strip(),
                    "phase": str(current.get("phase") or "").strip(),
                    "active": True,
                    "landing_url": str(current.get("landingPageUrl") or current.get("ctaUrl") or "").strip(),
                    "description": str(current.get("description") or current.get("headline") or "").strip(),
                    "deadline": current.get("countdownTarget"),
                    "label": str(current.get("ctaText") or current.get("countdownLabel") or "").strip(),
                }
            )
        programs = current.get("programs") if isinstance(current, dict) else root.get("programs")
        if isinstance(programs, dict):
            for key, program in programs.items():
                if not isinstance(program, dict):
                    continue
                landing = str(program.get("landingPageUrl") or "").strip()
                events.append(
                    {
                        "name": str(program.get("name") or _title_from_url(landing, str(key))).strip(),
                        "event_type": str(key or "hackathon").strip(),
                        "phase": str(program.get("phase") or program.get("label") or "").strip(),
                        "active": program.get("active"),
                        "landing_url": landing,
                        "description": str(program.get("label") or "").strip(),
                        "deadline": None,
                        "label": str(program.get("label") or "").strip(),
                    }
                )
    return events


def parse_listing(payload: dict[str, Any], source: OpportunitySource) -> list[RawOpportunity]:
    results: list[RawOpportunity] = []
    seen: set[str] = set()
    for event in _collect_events(payload):
        apply_url = _apply_url(str(event.get("landing_url") or ""))
        if not apply_url:
            continue
        phase = str(event.get("phase") or "")
        if not _is_open(phase, event.get("active")):
            continue
        slug = (urlparse(apply_url).path or "/").strip("/") or apply_url
        if slug in seen:
            continue
        title = str(event.get("name") or "").strip()[:255] or _title_from_url(apply_url, "Colosseum")
        event_type = str(event.get("event_type") or "hackathon").strip() or "hackathon"
        seen.add(slug)
        deadline = parse_iso_datetime(event.get("deadline"))
        description_parts = [
            "Official Colosseum Solana builder competition.",
            f"{event_type.replace('-', ' ').title()}.",
        ]
        if event.get("description"):
            description_parts.append(str(event["description"]).strip())
        if event.get("label"):
            description_parts.append(str(event["label"]).strip() + ".")
        description_parts.append("Apply on the Colosseum listing.")
        results.append(
            RawOpportunity(
                external_id=slug[:255],
                title=title,
                organization_name=source.name or "Colosseum",
                description=" ".join(part for part in description_parts if part)[:20000],
                location="Online",
                application_url=apply_url,
                source_url=apply_url,
                deadline=deadline,
                registration_deadline=deadline,
                opportunity_type=(
                    OpportunityType.CHALLENGE
                    if "challenge" in event_type.lower()
                    else OpportunityType.HACKATHON
                ),
                workplace_type=WorkplaceType.REMOTE,
                event_format=HackathonEventFormat.ONLINE,
                raw_data={
                    "event_type": event_type,
                    "phase": phase,
                    "path": urlparse(apply_url).path,
                },
            )
        )
        if len(results) >= MAX_EVENTS:
            break
    return results


def sanitize_listing_url(url: str) -> str:
    return canonicalize_path_url(
        url,
        allowed_hosts=COLOSSEUM_HOSTS,
        allowed_paths={"/hackathon", "/hackathon/__data.json"},
        canonical=DEFAULT_LISTING_URL,
        detail="Colosseum sources must use colosseum.com/hackathon",
    )


def fetch_listing_payload(url: str) -> dict[str, Any]:
    sanitize_listing_url(url)
    response = fetch_listing(
        DEFAULT_LISTING_URL,
        allowed_hosts=COLOSSEUM_HOSTS,
        accept="application/json",
        max_bytes=MAX_BODY_BYTES,
        failed_detail="Could not fetch Colosseum hackathon listing",
        redirected_detail="Colosseum request redirected away from colosseum.com",
        too_large_detail="Colosseum listing is too large to ingest",
    )
    payload = response.json()
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Colosseum returned an unexpected payload",
        )
    return payload


class ColosseumConnector:
    connector_type = "colosseum"

    def fetch(self, source: OpportunitySource) -> list[RawOpportunity]:
        url = str((source.config or {}).get("listing_url") or DEFAULT_LISTING_URL).strip()
        return parse_listing(fetch_listing_payload(url), source)
