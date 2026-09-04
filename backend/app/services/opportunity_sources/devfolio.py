from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.models.opportunity import HackathonEventFormat, OpportunitySource, OpportunityType, WorkplaceType
from app.services.opportunity_sources.base import MAX_BODY_BYTES, MAX_ITEMS_PER_SYNC, RawOpportunity
from app.services.opportunity_sources.listing_http import fetch_listing, parse_iso_datetime
from app.services.opportunity_sources.web3_filter import is_web3_text

DEVFOLIO_HOSTS = {"api.devfolio.co", "devfolio.co", "www.devfolio.co"}
DEFAULT_LISTING_URL = "https://api.devfolio.co/api/hackathons?filter=application_open&page=1&size=20"
MAX_EVENTS = 30


def _themes(row: dict[str, Any]) -> list[str]:
    themes = row.get("themes")
    if not isinstance(themes, list):
        return []
    names: list[str] = []
    for theme in themes:
        if isinstance(theme, dict):
            name = str(theme.get("name") or "").strip()
            if name:
                names.append(name)
        elif theme:
            names.append(str(theme).strip())
    return names


def _apply_url(row: dict[str, Any]) -> str | None:
    setting = row.get("hackathon_setting") if isinstance(row.get("hackathon_setting"), dict) else {}
    subdomain = str(setting.get("subdomain") or row.get("slug") or "").strip().lower()
    if not subdomain or not re_subdomain(subdomain):
        return None
    return f"https://{subdomain}.devfolio.co"


def re_subdomain(value: str) -> bool:
    return bool(value) and all(ch.isalnum() or ch in "-_" for ch in value) and value[0].isalnum()


def _workplace(row: dict[str, Any]) -> WorkplaceType:
    setting = row.get("hackathon_setting") if isinstance(row.get("hackathon_setting"), dict) else {}
    if setting.get("is_hybrid"):
        return WorkplaceType.HYBRID
    if row.get("is_online"):
        return WorkplaceType.REMOTE
    return WorkplaceType.ONSITE


def _location(row: dict[str, Any], workplace: WorkplaceType) -> str:
    if workplace == WorkplaceType.REMOTE:
        return "Online"
    parts = [str(row.get(key) or "").strip() for key in ("city", "state", "country")]
    return ", ".join(part for part in parts if part)[:255]


def parse_listing(payload: dict[str, Any], source: OpportunitySource) -> list[RawOpportunity]:
    rows = payload.get("result")
    if not isinstance(rows, list):
        return []
    results: list[RawOpportunity] = []
    seen: set[str] = set()
    for row in rows[:MAX_ITEMS_PER_SYNC]:
        if not isinstance(row, dict):
            continue
        title = str(row.get("name") or "").strip()[:255]
        slug = str(row.get("slug") or row.get("uuid") or "").strip()
        if not title or not slug or slug in seen:
            continue
        themes = _themes(row)
        if not is_web3_text(title, row.get("slug"), row.get("tagline"), row.get("desc"), themes):
            continue
        apply_url = _apply_url(row)
        if not apply_url:
            continue
        seen.add(slug)
        workplace = _workplace(row)
        location = _location(row, workplace)
        tagline = str(row.get("tagline") or "").strip()
        setting = row.get("hackathon_setting") if isinstance(row.get("hackathon_setting"), dict) else {}
        reg_deadline = parse_iso_datetime(setting.get("reg_ends_at"))
        start_at = parse_iso_datetime(row.get("starts_at") or setting.get("starts_at"))
        end_at = parse_iso_datetime(row.get("ends_at") or setting.get("ends_at"))
        deadline = reg_deadline or end_at
        format_map = {
            WorkplaceType.REMOTE: HackathonEventFormat.ONLINE,
            WorkplaceType.HYBRID: HackathonEventFormat.HYBRID,
            WorkplaceType.ONSITE: HackathonEventFormat.IN_PERSON,
        }
        parts = [
            "Official Devfolio hackathon matching Analytic Sages Web3 filters.",
            tagline + "." if tagline else "",
            location + "." if location else "",
            "Apply on the Devfolio listing.",
        ]
        results.append(
            RawOpportunity(
                external_id=slug[:255],
                title=title,
                organization_name=source.name or "Devfolio",
                description=" ".join(part for part in parts if part)[:20000],
                location=location,
                application_url=apply_url,
                source_url=apply_url,
                deadline=deadline,
                registration_deadline=reg_deadline or deadline,
                start_at=start_at,
                end_at=end_at,
                opportunity_type=OpportunityType.HACKATHON,
                workplace_type=workplace,
                event_format=format_map.get(workplace, HackathonEventFormat.UNKNOWN),
                tags=themes,
                raw_data={"slug": slug, "themes": themes, "uuid": row.get("uuid")},
            )
        )
        if len(results) >= MAX_EVENTS:
            break
    return results


def sanitize_listing_url(url: str) -> str:
    from urllib.parse import urlparse

    cleaned = url.strip() or DEFAULT_LISTING_URL
    parsed = urlparse(cleaned)
    host = (parsed.hostname or "").lower()
    if host not in DEVFOLIO_HOSTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Devfolio sources must use api.devfolio.co hackathon listings",
        )
    path = (parsed.path or "/").rstrip("/") or "/"
    if path not in {"/api/hackathons", "/explore"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Devfolio sources must use the open hackathons listing",
        )
    return DEFAULT_LISTING_URL


def fetch_listing_payload(url: str) -> dict[str, Any]:
    sanitize_listing_url(url)
    response = fetch_listing(
        DEFAULT_LISTING_URL,
        allowed_hosts=DEVFOLIO_HOSTS,
        accept="application/json",
        max_bytes=MAX_BODY_BYTES,
        failed_detail="Could not fetch Devfolio hackathon listing",
        redirected_detail="Devfolio request redirected away from api.devfolio.co",
        too_large_detail="Devfolio listing is too large to ingest",
    )
    payload = response.json()
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Devfolio returned an unexpected payload",
        )
    return payload


class DevfolioConnector:
    connector_type = "devfolio"

    def fetch(self, source: OpportunitySource) -> list[RawOpportunity]:
        url = str((source.config or {}).get("listing_url") or DEFAULT_LISTING_URL).strip()
        return parse_listing(fetch_listing_payload(url), source)
