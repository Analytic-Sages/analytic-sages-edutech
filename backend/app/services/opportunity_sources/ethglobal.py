from __future__ import annotations

import calendar
import html
import logging
import re
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, status

from app.models.opportunity import HackathonEventFormat, OpportunitySource, OpportunityType, WorkplaceType
from app.services.opportunity_sources.base import (
    FETCH_TIMEOUT_SECONDS,
    USER_AGENT,
    RawOpportunity,
)
from app.services.opportunity_urls import hostname_of, validate_http_url

logger = logging.getLogger(__name__)

ETHGLOBAL_HOSTS = {"ethglobal.com", "www.ethglobal.com"}
DEFAULT_EVENTS_URL = "https://ethglobal.com/events"
MAX_EVENTS_BODY_BYTES = 4_000_000
MAX_EVENTS = 30

ALLOWED_LABELS = {
    "hackathon": "Hackathon",
    "async hackathon": "Async Hackathon",
    "irl hackathon": "IRL Hackathon",
}

COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")
PAST_HEADING_RE = re.compile(r"<h2\b[^>]*>\s*Past\b", re.I)
CARD_RE = re.compile(
    r'<a\b[^>]*href="(/events/([a-zA-Z0-9][a-zA-Z0-9_-]*))"[^>]*>(.*?)</a>',
    re.I | re.S,
)
TYPE_RE = re.compile(r">\s*((?:IRL|Async)\s+Hackathon|Hackathon)\s*<", re.I)
TITLE_RE = re.compile(r"<h2\b[^>]*>(.*?)</h2>", re.I | re.S)
MONTH_RE = re.compile(
    r"tracking-wider\">\s*("
    r"January|February|March|April|May|June|July|August|September|October|November|December"
    r")\s*</div>",
    re.I,
)
DAY_SPAN_RE = re.compile(r'<span class="">\s*(\d{1,2})\s*</span>')
YEAR_RE = re.compile(r"\b(20\d{2})\b")
SLUG_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,80}$")


def _plain(value: str) -> str:
    text = COMMENT_RE.sub(" ", value)
    text = TAG_RE.sub(" ", html.unescape(text))
    text = WHITESPACE_RE.sub(" ", text).strip()
    return re.sub(r"\s+,", ",", text)


def _label(value: str) -> str | None:
    key = WHITESPACE_RE.sub(" ", value).strip().lower()
    return ALLOWED_LABELS.get(key)


def _location(card_html: str) -> str:
    for match in re.finditer(r'<span class="">(.*?)</span>', card_html, re.S):
        text = _plain(match.group(1))
        if not text or _label(text):
            continue
        if "," in text or text.lower() in {"online", "remote"}:
            return text[:255]
    return ""


def _event_dates(card_html: str, title: str) -> tuple[str, datetime | None, datetime | None]:
    header = card_html.split("<h2", 1)[0]
    month_match = MONTH_RE.search(header)
    days = [int(day) for day in DAY_SPAN_RE.findall(header)]
    year_match = YEAR_RE.search(title)
    year = int(year_match.group(1)) if year_match else datetime.now(UTC).year
    if not month_match or not days:
        return "", None, None
    month_name = month_match.group(1).title()
    month = list(calendar.month_name).index(month_name)
    start_day = days[0]
    end_day = days[-1]
    try:
        start = datetime(year, month, start_day, 0, 0, 0, tzinfo=UTC)
        end = datetime(year, month, end_day, 23, 59, 59, tzinfo=UTC)
    except ValueError:
        return f"{month_name} {start_day}–{end_day} {year}", None, None
    if start_day == end_day:
        label = f"{month_name} {start_day}, {year}"
    else:
        label = f"{month_name} {start_day}–{end_day}, {year}"
    return label, start, end


def _workplace(label: str, location: str) -> WorkplaceType:
    key = label.lower()
    if key == "async hackathon":
        return WorkplaceType.REMOTE
    loc = location.lower()
    if "online" in loc or loc == "remote":
        return WorkplaceType.REMOTE
    return WorkplaceType.ONSITE


def parse_listing(page_html: str, source: OpportunitySource) -> list[RawOpportunity]:
    upcoming = PAST_HEADING_RE.split(page_html, maxsplit=1)[0]
    results: list[RawOpportunity] = []
    seen: set[str] = set()
    for match in CARD_RE.finditer(upcoming):
        slug = match.group(2)
        if not SLUG_RE.fullmatch(slug) or slug in seen:
            continue
        card = match.group(3)
        type_match = TYPE_RE.search(card)
        if not type_match:
            continue
        label = _label(type_match.group(1))
        if not label:
            continue
        title_match = TITLE_RE.search(card)
        title = _plain(title_match.group(1))[:255] if title_match else ""
        if not title:
            continue
        seen.add(slug)
        path = f"/events/{slug}"
        application_url = f"https://ethglobal.com{path}"
        location = _location(card)
        if not location and label.lower() == "async hackathon":
            location = "Online"
        date_label, start_at, end_at = _event_dates(card, title)
        description_parts = [
            f"Official ETHGlobal {label} for Ethereum and Web3 builders.",
        ]
        if location:
            description_parts.append(location + ".")
        if date_label:
            description_parts.append(date_label + ".")
        description_parts.append("Apply on the ETHGlobal events page.")
        workplace = _workplace(label, location)
        format_map = {
            WorkplaceType.REMOTE: HackathonEventFormat.ONLINE,
            WorkplaceType.HYBRID: HackathonEventFormat.HYBRID,
            WorkplaceType.ONSITE: HackathonEventFormat.IN_PERSON,
        }
        results.append(
            RawOpportunity(
                external_id=slug[:255],
                title=title,
                organization_name=source.name or "ETHGlobal",
                description=" ".join(description_parts),
                location=location,
                application_url=application_url,
                source_url=application_url,
                deadline=end_at,
                registration_deadline=end_at,
                start_at=start_at,
                end_at=end_at,
                opportunity_type=OpportunityType.HACKATHON,
                workplace_type=workplace,
                event_format=format_map.get(workplace, HackathonEventFormat.UNKNOWN),
                raw_data={
                    "slug": slug,
                    "ethglobal_type": label,
                    "path": path,
                    "date_label": date_label,
                },
            )
        )
        if len(results) >= MAX_EVENTS:
            break
    return results


def _events_url(source: OpportunitySource) -> str:
    raw = str((source.config or {}).get("events_url") or DEFAULT_EVENTS_URL).strip()
    return sanitize_events_url(raw)


def sanitize_events_url(url: str) -> str:
    cleaned = validate_http_url(url, "events_url")
    parsed = urlparse(cleaned)
    host = (parsed.hostname or "").lower()
    if host not in ETHGLOBAL_HOSTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ETHGlobal sources must use ethglobal.com/events",
        )
    path = (parsed.path or "/").rstrip("/") or "/"
    if path != "/events":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ETHGlobal sources must use the main /events listing",
        )
    return f"https://ethglobal.com/events"


def fetch_listing(url: str) -> str:
    sanitize_events_url(url)
    try:
        with httpx.Client(
            timeout=FETCH_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
        ) as client:
            response = client.get(url)
            final_host = hostname_of(str(response.url))
            if final_host not in ETHGLOBAL_HOSTS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ETHGlobal request redirected away from ethglobal.com",
                )
            response.raise_for_status()
            if len(response.content) > MAX_EVENTS_BODY_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="ETHGlobal events page is too large to ingest",
                )
            return response.text
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        logger.warning("ETHGlobal fetch failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch ETHGlobal events",
        ) from exc


class EthglobalConnector:
    connector_type = "ethglobal"

    def fetch(self, source: OpportunitySource) -> list[RawOpportunity]:
        url = _events_url(source)
        return parse_listing(fetch_listing(url), source)
