from __future__ import annotations

import html
import json
import re

from app.models.opportunity import OpportunitySource, OpportunityType, WorkplaceType
from app.services.opportunity_sources.listing_http import canonicalize_path_url, fetch_listing
from app.services.opportunity_sources.base import RawOpportunity

DORAHACKS_HOSTS = {"dorahacks.io", "www.dorahacks.io"}
DEFAULT_LISTING_URL = "https://dorahacks.io/hackathon?status=upcoming"
MAX_EVENTS = 30
MAX_BODY_BYTES = 4_000_000
SLUG_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,80}$")
PATH_RE = re.compile(r'"/hackathon/([a-zA-Z0-9][a-zA-Z0-9_-]{0,80})/"')
NUXT_RE = re.compile(
    r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
    re.I | re.S,
)


def _title_from_slug(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").strip().title()[:255]


def parse_listing(page_html: str, source: OpportunitySource) -> list[RawOpportunity]:
    payload_html = page_html
    nuxt = NUXT_RE.search(page_html)
    if nuxt:
        payload_html = html.unescape(nuxt.group(1))
        try:
            json.loads(payload_html)
        except json.JSONDecodeError:
            payload_html = page_html
    results: list[RawOpportunity] = []
    seen: set[str] = set()
    for slug in PATH_RE.findall(payload_html):
        if not SLUG_RE.fullmatch(slug) or slug in seen:
            continue
        seen.add(slug)
        apply_url = f"https://dorahacks.io/hackathon/{slug}"
        title = _title_from_slug(slug)
        results.append(
            RawOpportunity(
                external_id=slug[:255],
                title=title,
                organization_name=source.name or "DoraHacks",
                description=(
                    "Official DoraHacks upcoming hackathon for multi-chain Web3 builders. "
                    "Apply on the DoraHacks listing."
                ),
                location="",
                application_url=apply_url,
                source_url=apply_url,
                opportunity_type=OpportunityType.HACKATHON,
                workplace_type=WorkplaceType.REMOTE,
                raw_data={"slug": slug, "path": f"/hackathon/{slug}"},
            )
        )
        if len(results) >= MAX_EVENTS:
            break
    return results


def sanitize_listing_url(url: str) -> str:
    return canonicalize_path_url(
        url,
        allowed_hosts=DORAHACKS_HOSTS,
        allowed_paths={"/hackathon"},
        canonical=DEFAULT_LISTING_URL,
        detail="DoraHacks sources must use dorahacks.io/hackathon",
    )


def fetch_listing_html(url: str) -> str:
    sanitize_listing_url(url)
    response = fetch_listing(
        DEFAULT_LISTING_URL,
        allowed_hosts=DORAHACKS_HOSTS,
        accept="text/html,application/json",
        max_bytes=MAX_BODY_BYTES,
        failed_detail="Could not fetch DoraHacks listing (blocked or unavailable)",
        redirected_detail="DoraHacks request redirected away from dorahacks.io",
        too_large_detail="DoraHacks listing is too large to ingest",
        extra_headers={"Referer": "https://dorahacks.io/hackathon"},
    )
    return response.text


class DorahacksConnector:
    connector_type = "dorahacks"

    def fetch(self, source: OpportunitySource) -> list[RawOpportunity]:
        url = str((source.config or {}).get("listing_url") or DEFAULT_LISTING_URL).strip()
        return parse_listing(fetch_listing_html(url), source)
