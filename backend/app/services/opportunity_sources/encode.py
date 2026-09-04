from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from fastapi import HTTPException, status

from app.models.opportunity import OpportunitySource, OpportunityType, WorkplaceType
from app.services.opportunity_sources.base import MAX_BODY_BYTES, MAX_ITEMS_PER_SYNC, RawOpportunity
from app.services.opportunity_sources.listing_http import fetch_listing, parse_iso_datetime
from app.services.opportunity_urls import hostname_of, validate_http_url

ENCODE_HOSTS = {
    "www.encodeclub.com",
    "encodeclub.com",
    "encode.club",
    "www.encode.club",
}
DEFAULT_LISTING_URL = "https://www.encodeclub.com/programmes"
MAX_EVENTS = 30
HACKATHON_TYPES = {"hackathon", "in-person hackathon", "in person hackathon"}
BOUNTY_TYPES = {"bounty"}
APPLY_HOSTS = {
    "encodeclub.com",
    "www.encodeclub.com",
    "encode.club",
    "www.encode.club",
    "lu.ma",
    "luma.com",
}


def _encode_date(value: object) -> datetime | None:
    parsed = parse_iso_datetime(value)
    if parsed:
        return parsed
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%d %B %Y", "%d %b %Y", "%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def _type_for(label: str) -> OpportunityType | None:
    key = label.strip().lower()
    if key in HACKATHON_TYPES:
        return OpportunityType.HACKATHON
    if key in BOUNTY_TYPES:
        return OpportunityType.BOUNTY
    return None


def _apply_url(row: dict[str, Any]) -> str | None:
    for key in ("website_url", "registration_url"):
        url = str(row.get(key) or "").strip()
        if not url:
            continue
        try:
            validate_http_url(url, "application_url")
        except HTTPException:
            continue
        host = hostname_of(url)
        if host and (host in APPLY_HOSTS or host.endswith(".encode.club") or host.endswith(".encodeclub.com")):
            return url
    return None


def parse_listing(rows: list[Any], source: OpportunitySource, *, now: datetime | None = None) -> list[RawOpportunity]:
    moment = now or datetime.now(UTC)
    results: list[RawOpportunity] = []
    seen: set[str] = set()
    for row in rows[:MAX_ITEMS_PER_SYNC]:
        if not isinstance(row, dict):
            continue
        title = str(row.get("official_name") or "").strip()[:255]
        encode_id = str(row.get("encode_id") or "").strip()
        program_type = str(row.get("type") or "").strip()
        mapped = _type_for(program_type)
        if not title or not encode_id or encode_id in seen or mapped is None:
            continue
        end = _encode_date(row.get("end_date"))
        if end is None or end < moment:
            continue
        apply_url = _apply_url(row)
        if not apply_url:
            continue
        seen.add(encode_id)
        workplace = WorkplaceType.ONSITE if "person" in program_type.lower() else WorkplaceType.REMOTE
        location = "" if workplace == WorkplaceType.ONSITE else "Online"
        start = _encode_date(row.get("start_date"))
        date_label = ""
        if start and end:
            date_label = f"{start.date().isoformat()} to {end.date().isoformat()}."
        results.append(
            RawOpportunity(
                external_id=encode_id[:255],
                title=title,
                organization_name=source.name or "Encode Club",
                description=(
                    f"Official Encode Club {program_type} for Web3 and AI builders. "
                    f"{date_label} Apply on the Encode listing."
                ),
                location=location,
                application_url=apply_url,
                source_url=apply_url,
                deadline=end.replace(hour=23, minute=59, second=59),
                opportunity_type=mapped,
                workplace_type=workplace,
                raw_data={"encode_id": encode_id, "programme_type": program_type},
            )
        )
        if len(results) >= MAX_EVENTS:
            break
    return results


def sanitize_listing_url(url: str) -> str:
    cleaned = validate_http_url(url.strip() or DEFAULT_LISTING_URL, "listing_url")
    parsed = urlparse(cleaned)
    host = (parsed.hostname or "").lower()
    if host not in ENCODE_HOSTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Encode sources must use encodeclub.com/programmes",
        )
    path = (parsed.path or "/").rstrip("/") or "/"
    if path not in {"/programmes", "/hackathons"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Encode sources must use the programmes listing",
        )
    return DEFAULT_LISTING_URL


def fetch_listing_rows(url: str) -> list[Any]:
    sanitize_listing_url(url)
    response = fetch_listing(
        DEFAULT_LISTING_URL,
        allowed_hosts=ENCODE_HOSTS,
        accept="application/json,text/html",
        max_bytes=MAX_BODY_BYTES,
        failed_detail="Could not fetch Encode programmes listing",
        redirected_detail="Encode request redirected away from encodeclub.com",
        too_large_detail="Encode listing is too large to ingest",
    )
    text = response.text.lstrip()
    if text.startswith("[") or text.startswith("{"):
        payload = response.json()
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get("programmes"), list):
            return payload["programmes"]
    # The public programmes page is a client-rendered shell with no listing rows.
    return []


class EncodeConnector:
    connector_type = "encode"

    def fetch(self, source: OpportunitySource) -> list[RawOpportunity]:
        url = str((source.config or {}).get("listing_url") or DEFAULT_LISTING_URL).strip()
        return parse_listing(fetch_listing_rows(url), source)
