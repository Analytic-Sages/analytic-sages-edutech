from __future__ import annotations

import html
import re
from urllib.parse import urlparse

from app.models.opportunity import OpportunitySource, OpportunityType, WorkplaceType
from app.services.opportunity_sources.base import RawOpportunity
from app.services.opportunity_sources.listing_http import canonicalize_path_url, fetch_listing
DEVPOST_HOSTS = {"devpost.com", "www.devpost.com"}
DEFAULT_LISTING_URL = "https://devpost.com/c/blockchain"
MAX_EVENTS = 30
MAX_BODY_BYTES = 4_000_000
SKIP_SUBDOMAINS = {"help", "info", "www", "secure", "api", "status"}
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")
CURRENT_END_RE = re.compile(
    r"<h2\b[^>]*>\s*(?:Top Blockchain builders|Recent winning Blockchain|Recent Blockchain hackathons)\b",
    re.I,
)
CARD_RE = re.compile(
    r'<article class="hackathon-tile[^"]*"\s*>\s*'
    r'<a\b[^>]*href="(https://([a-z0-9-]+)\.devpost\.com/?)"[^>]*>(.*?)</a>',
    re.I | re.S,
)
TITLE_RE = re.compile(r'<h5 class="title">\s*(.*?)\s*</h5>', re.I | re.S)
DESC_RE = re.compile(r'<p class="challenge-description">\s*(.*?)\s*</p>', re.I | re.S)
LOC_RE = re.compile(r'<p class="challenge-location">\s*(.*?)\s*</p>', re.I | re.S)


def _plain(value: str) -> str:
    text = COMMENT_RE.sub(" ", value)
    text = TAG_RE.sub(" ", html.unescape(text))
    return WHITESPACE_RE.sub(" ", text).strip()


def parse_listing(page_html: str, source: OpportunitySource) -> list[RawOpportunity]:
    current = CURRENT_END_RE.split(page_html, maxsplit=1)[0]
    results: list[RawOpportunity] = []
    seen: set[str] = set()
    for match in CARD_RE.finditer(current):
        apply_url = match.group(1).rstrip("/") + "/"
        subdomain = match.group(2).lower()
        if subdomain in SKIP_SUBDOMAINS or subdomain in seen:
            continue
        card = match.group(3)
        title_match = TITLE_RE.search(card)
        title = _plain(title_match.group(1))[:255] if title_match else ""
        if not title:
            continue
        seen.add(subdomain)
        description = _plain(DESC_RE.search(card).group(1)) if DESC_RE.search(card) else ""
        location = _plain(LOC_RE.search(card).group(1)) if LOC_RE.search(card) else ""
        loc_key = location.lower()
        workplace = WorkplaceType.REMOTE if "online" in loc_key or loc_key == "remote" else WorkplaceType.ONSITE
        if not location and workplace == WorkplaceType.REMOTE:
            location = "Online"
        parts = [
            "Official Devpost blockchain hackathon.",
            description + "." if description else "",
            location + "." if location else "",
            "Apply on the Devpost listing.",
        ]
        results.append(
            RawOpportunity(
                external_id=subdomain[:255],
                title=title,
                organization_name=source.name or "Devpost",
                description=" ".join(part for part in parts if part)[:20000],
                location=location[:255],
                application_url=apply_url,
                source_url=apply_url,
                opportunity_type=OpportunityType.HACKATHON,
                workplace_type=workplace,
                raw_data={"subdomain": subdomain, "path": urlparse(apply_url).path},
            )
        )
        if len(results) >= MAX_EVENTS:
            break
    return results


def sanitize_listing_url(url: str) -> str:
    return canonicalize_path_url(
        url,
        allowed_hosts=DEVPOST_HOSTS,
        allowed_paths={"/c/blockchain"},
        canonical=DEFAULT_LISTING_URL,
        detail="Devpost sources must use devpost.com/c/blockchain",
    )


def fetch_listing_html(url: str) -> str:
    sanitize_listing_url(url)
    response = fetch_listing(
        DEFAULT_LISTING_URL,
        allowed_hosts=DEVPOST_HOSTS,
        accept="text/html",
        max_bytes=MAX_BODY_BYTES,
        failed_detail="Could not fetch Devpost blockchain listing",
        redirected_detail="Devpost request redirected away from devpost.com",
        too_large_detail="Devpost listing is too large to ingest",
    )
    return response.text


class DevpostConnector:
    connector_type = "devpost"

    def fetch(self, source: OpportunitySource) -> list[RawOpportunity]:
        url = str((source.config or {}).get("listing_url") or DEFAULT_LISTING_URL).strip()
        return parse_listing(fetch_listing_html(url), source)
