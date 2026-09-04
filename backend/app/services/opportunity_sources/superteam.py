from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.models.opportunity import OpportunitySource, OpportunityType, WorkplaceType
from app.services.opportunity_sources.base import MAX_BODY_BYTES, MAX_ITEMS_PER_SYNC, RawOpportunity
from app.services.opportunity_sources.listing_http import (
    canonicalize_path_url,
    fetch_listing,
    parse_iso_datetime,
)

SUPERTEAM_HOSTS = {"superteam.fun", "www.superteam.fun", "earn.superteam.fun"}
DEFAULT_LISTING_URL = "https://superteam.fun/api/listings"
MAX_EVENTS = 50
TYPE_MAP = {
    "hackathon": OpportunityType.HACKATHON,
    "bounty": OpportunityType.BOUNTY,
    "project": OpportunityType.GRANT,
}
SLUG_ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")


def _slug_ok(slug: str) -> bool:
    return bool(slug) and slug[0].isalnum() and all(ch in SLUG_ALLOWED for ch in slug) and len(slug) <= 120


def _opportunity_type(value: object) -> OpportunityType | None:
    return TYPE_MAP.get(str(value or "").strip().lower())


def parse_listing(rows: list[Any], source: OpportunitySource) -> list[RawOpportunity]:
    from decimal import Decimal

    from app.services.bounty_normalize import infer_bounty_category

    results: list[RawOpportunity] = []
    seen: set[str] = set()
    for row in rows[:MAX_ITEMS_PER_SYNC]:
        if not isinstance(row, dict):
            continue
        mapped = _opportunity_type(row.get("type"))
        status_value = str(row.get("status") or "").strip().upper()
        slug = str(row.get("slug") or "").strip()
        title = str(row.get("title") or "").strip()[:255]
        listing_id = str(row.get("id") or slug).strip()
        if mapped is None or status_value != "OPEN" or row.get("isWinnersAnnounced") or not title:
            continue
        if not _slug_ok(slug) or slug in seen:
            continue
        seen.add(slug)
        apply_url = f"https://superteam.fun/earn/listing/{slug}"
        sponsor = row.get("sponsor") if isinstance(row.get("sponsor"), dict) else {}
        org = str(sponsor.get("name") or source.name or "Superteam Earn").strip()[:255]
        reward = row.get("rewardAmount")
        token = str(row.get("token") or "").strip()
        reward_amount = None
        if reward not in (None, ""):
            try:
                reward_amount = Decimal(str(reward))
            except Exception:
                reward_amount = None
        reward_label = ""
        if reward_amount is not None:
            reward_label = f" Reward {reward_amount} {token}.".replace("  ", " ")
        type_label = str(row.get("type") or mapped.value).title()
        location = "Nigeria" if "nigeria" in org.lower() else "Online"
        deadline = parse_iso_datetime(row.get("deadline"))
        skills = []
        raw_skills = row.get("skills")
        if isinstance(raw_skills, list):
            skills = [str(s).strip() for s in raw_skills if str(s).strip()][:12]
        results.append(
            RawOpportunity(
                external_id=(listing_id or slug)[:255],
                title=title,
                organization_name=org,
                description=(
                    f"Official Superteam Earn {type_label} from {org}.{reward_label} "
                    "Apply on the Superteam Earn listing."
                ),
                location=location,
                application_url=apply_url,
                source_url=apply_url,
                deadline=deadline,
                opportunity_type=mapped,
                workplace_type=WorkplaceType.REMOTE,
                reward_amount=reward_amount if mapped == OpportunityType.BOUNTY else None,
                reward_token=token[:32] if token and mapped == OpportunityType.BOUNTY else None,
                reward_raw=(
                    f"{reward_amount} {token}".strip()
                    if mapped == OpportunityType.BOUNTY and reward_amount is not None
                    else None
                ),
                bounty_category=(
                    infer_bounty_category(title, type_label, str(row.get("type") or ""))
                    if mapped == OpportunityType.BOUNTY
                    else None
                ),
                bounty_deadline=deadline if mapped == OpportunityType.BOUNTY else None,
                winners_announced=bool(row.get("isWinnersAnnounced"))
                if mapped == OpportunityType.BOUNTY
                else None,
                bounty_skills=skills if mapped == OpportunityType.BOUNTY else [],
                tags=skills if mapped == OpportunityType.BOUNTY else [],
                raw_data={
                    "slug": slug,
                    "listing_type": row.get("type"),
                    "status": status_value,
                    "rewardAmount": reward,
                    "token": token,
                    "isWinnersAnnounced": row.get("isWinnersAnnounced"),
                    "skills": skills,
                },
            )
        )
        if len(results) >= MAX_EVENTS:
            break
    return results


def sanitize_listing_url(url: str) -> str:
    return canonicalize_path_url(
        url,
        allowed_hosts=SUPERTEAM_HOSTS,
        allowed_paths={"/api/listings", "/earn", "/earn/"},
        canonical=DEFAULT_LISTING_URL,
        detail="Superteam sources must use superteam.fun/api/listings",
    )


def fetch_listing_rows(url: str) -> list[Any]:
    sanitize_listing_url(url)
    response = fetch_listing(
        DEFAULT_LISTING_URL,
        allowed_hosts=SUPERTEAM_HOSTS,
        accept="application/json",
        max_bytes=MAX_BODY_BYTES,
        failed_detail="Could not fetch Superteam Earn listings",
        redirected_detail="Superteam request redirected away from superteam.fun",
        too_large_detail="Superteam listing is too large to ingest",
    )
    payload = response.json()
    if not isinstance(payload, list):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Superteam returned an unexpected payload",
        )
    return payload


class SuperteamConnector:
    connector_type = "superteam"

    def fetch(self, source: OpportunitySource) -> list[RawOpportunity]:
        url = str((source.config or {}).get("listing_url") or DEFAULT_LISTING_URL).strip()
        return parse_listing(fetch_listing_rows(url), source)
