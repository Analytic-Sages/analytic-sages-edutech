from __future__ import annotations

import html
import logging
import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

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
from app.services.opportunity_urls import hostname_of, validate_http_url

logger = logging.getLogger(__name__)
TAG_RE = re.compile(r"<[^>]+>")


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    return html.unescape(TAG_RE.sub(" ", value)).replace("\xa0", " ")


def _collapse(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1].lower()


def _child_text(element: ElementTree.Element, names: set[str]) -> str:
    for child in list(element):
        if _local(child.tag) in names:
            text = "".join(child.itertext())
            if text and text.strip():
                return text
    return ""


def _link(element: ElementTree.Element) -> str:
    for child in list(element):
        if _local(child.tag) != "link":
            continue
        href = (child.attrib.get("href") or "").strip()
        if href:
            return href
        text = (child.text or "").strip()
        if text:
            return text
    guid = _child_text(element, {"guid", "id"})
    return guid.strip()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value or not value.strip():
        return None
    raw = value.strip()
    try:
        parsed = parsedate_to_datetime(raw)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        iso = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if iso.tzinfo is None:
            return iso.replace(tzinfo=UTC)
        return iso.astimezone(UTC)
    except ValueError:
        return None


def parse_feed(xml_text: str, source: OpportunitySource) -> list[RawOpportunity]:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not parse RSS feed: {exc}",
        ) from exc

    items: list[ElementTree.Element] = []
    if _local(root.tag) in {"rss", "rdf"}:
        items = [node for node in root.iter() if _local(node.tag) == "item"]
    elif _local(root.tag) == "feed":
        items = [node for node in list(root) if _local(node.tag) == "entry"]
    else:
        items = [node for node in root.iter() if _local(node.tag) in {"item", "entry"}]

    results: list[RawOpportunity] = []
    for index, item in enumerate(items[:MAX_ITEMS_PER_SYNC]):
        title = _collapse(strip_html(_child_text(item, {"title"})))[:255]
        description = _collapse(
            strip_html(
                _child_text(item, {"content", "encoded", "description", "summary"})
                or (item.text or "")
            )
        )[:20000]
        link = _link(item).strip()
        guid = _collapse(_child_text(item, {"guid", "id"})) or link or f"rss-{index}"
        posted = _parse_datetime(_child_text(item, {"pubdate", "published", "updated", "date"}))
        if not title:
            continue
        application_url = link or (source.website_url or "")
        results.append(
            RawOpportunity(
                external_id=guid[:255],
                title=title,
                organization_name=source.name,
                description=description,
                location="",
                application_url=application_url,
                source_url=link or None,
                posted_at=posted,
                raw_data={"guid": guid, "link": link},
            )
        )
    return results


def fetch_text(url: str) -> str:
    validated = validate_http_url(url, "feed_url")
    try:
        with httpx.Client(
            timeout=FETCH_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*"},
        ) as client:
            response = client.get(validated)
            final_url = str(response.url)
            if not hostname_of(final_url) or hostname_of(final_url) in {"localhost", "127.0.0.1"}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="feed_url redirected to a blocked host",
                )
            validate_http_url(final_url, "feed_url")
            response.raise_for_status()
            body = response.content
            if len(body) > MAX_BODY_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="RSS feed is too large to ingest",
                )
            return body.decode(response.encoding or "utf-8", errors="replace")
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        logger.warning("RSS fetch failed for %s: %s", url, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch RSS feed",
        ) from exc


class RssConnector:
    connector_type = "rss"

    def fetch(self, source: OpportunitySource) -> list[RawOpportunity]:
        feed_url = str((source.config or {}).get("feed_url") or "").strip()
        if not feed_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RSS sources require config.feed_url",
            )
        return parse_feed(fetch_text(feed_url), source)
