"""Normalize hackathon-specific fields from RawOpportunity payloads."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.models.opportunity import HackathonEventFormat, OpportunityType, WorkplaceType
from app.services.hackathon_dates import HackathonPhase, derive_hackathon_phase
from app.services.opportunity_sources.base import RawOpportunity

PRIZE_RE = re.compile(
    r"(?:\$|usd\s*)?\s*([\d][\d,]*(?:\.\d+)?)\s*(k|m|million|thousand)?\s*(?:usd|usdc|\$)?",
    re.I,
)
TEAM_RE = re.compile(r"(?:teams?\s+of\s+|team\s+size[:\s]+|up\s+to\s+)(\d+)(?:\s*[-–]\s*(\d+))?", re.I)


@dataclass
class HackathonDetailsPayload:
    short_description: str | None = None
    registration_url: str | None = None
    website_url: str | None = None
    registration_open_at: datetime | None = None
    registration_deadline: datetime | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    submission_deadline: datetime | None = None
    announcement_at: datetime | None = None
    event_format: HackathonEventFormat = HackathonEventFormat.UNKNOWN
    prize_pool_amount: Decimal | None = None
    prize_currency: str | None = None
    prize_pool_raw: str | None = None
    team_size_min: int | None = None
    team_size_max: int | None = None
    team_required: bool = False
    individual_allowed: bool = True
    tags: list[str] = field(default_factory=list)
    tracks: list[str] = field(default_factory=list)
    technology_focus: str | None = None
    derived_phase: str = HackathonPhase.UNKNOWN.value
    opportunity_type: OpportunityType = OpportunityType.HACKATHON


def event_format_from_workplace(
    workplace: WorkplaceType | None,
    *,
    location: str = "",
    label: str = "",
) -> HackathonEventFormat:
    blob = f"{location} {label}".lower()
    if "hybrid" in blob or workplace == WorkplaceType.HYBRID:
        return HackathonEventFormat.HYBRID
    if workplace == WorkplaceType.REMOTE or any(
        token in blob for token in ("online", "remote", "async", "virtual")
    ):
        return HackathonEventFormat.ONLINE
    if workplace == WorkplaceType.ONSITE or any(
        token in blob for token in ("irl", "in-person", "in person", "onsite", "on-site")
    ):
        return HackathonEventFormat.IN_PERSON
    return HackathonEventFormat.UNKNOWN


def parse_prize(text: str | None) -> tuple[Decimal | None, str | None, str | None]:
    if not text:
        return None, None, None
    cleaned = str(text).strip()[:255]
    match = PRIZE_RE.search(cleaned.replace(",", ""))
    if not match:
        return None, None, cleaned or None
    try:
        amount = Decimal(match.group(1).replace(",", ""))
    except (InvalidOperation, ValueError):
        return None, None, cleaned
    suffix = (match.group(2) or "").lower()
    if suffix in {"k", "thousand"}:
        amount *= Decimal(1000)
    elif suffix in {"m", "million"}:
        amount *= Decimal(1_000_000)
    currency = "USD" if "$" in cleaned or "usd" in cleaned.lower() else None
    return amount, currency, cleaned


def parse_team_size(blob: str) -> tuple[int | None, int | None, bool, bool]:
    match = TEAM_RE.search(blob)
    if not match:
        individual = "individual" in blob.lower() or "solo" in blob.lower()
        required = "team required" in blob.lower() or "teams only" in blob.lower()
        return None, None, required, not required or individual
    low = int(match.group(1))
    high = int(match.group(2)) if match.group(2) else low
    return low, high, True, low <= 1


def _pick_dt(raw: RawOpportunity, *keys: str) -> datetime | None:
    data = raw.raw_data if isinstance(raw.raw_data, dict) else {}
    for key in keys:
        value = getattr(raw, key, None) if hasattr(raw, key) else None
        if value is None:
            value = data.get(key)
        if isinstance(value, datetime):
            return value
    # Direct optional fields on RawOpportunity
    for attr in keys:
        if hasattr(raw, attr):
            value = getattr(raw, attr)
            if isinstance(value, datetime):
                return value
    return None


def normalize_hackathon_details(
    raw: RawOpportunity,
    *,
    now: datetime | None = None,
) -> HackathonDetailsPayload:
    data: dict[str, Any] = raw.raw_data if isinstance(raw.raw_data, dict) else {}
    description = (raw.description or "")[:500]
    blob = f"{raw.title} {raw.description} {raw.location}".lower()

    registration_deadline = (
        getattr(raw, "registration_deadline", None)
        or data.get("registration_deadline")
        or data.get("reg_ends_at")
        or raw.deadline
    )
    if not isinstance(registration_deadline, datetime):
        registration_deadline = raw.deadline

    start_at = getattr(raw, "start_at", None) or data.get("start_at") or data.get("starts_at")
    end_at = getattr(raw, "end_at", None) or data.get("end_at") or data.get("ends_at")
    if not isinstance(start_at, datetime):
        start_at = None
    if not isinstance(end_at, datetime):
        end_at = None

    submission = getattr(raw, "submission_deadline", None) or data.get("submission_deadline")
    if not isinstance(submission, datetime):
        submission = None

    reg_open = getattr(raw, "registration_open_at", None) or data.get("registration_open_at")
    if not isinstance(reg_open, datetime):
        reg_open = None

    workplace = raw.workplace_type
    label = str(data.get("ethglobal_type") or data.get("format") or data.get("event_type") or "")
    event_format = getattr(raw, "event_format", None)
    if not isinstance(event_format, HackathonEventFormat):
        event_format = event_format_from_workplace(workplace, location=raw.location or "", label=label)

    prize_raw = getattr(raw, "prize_pool_raw", None) or data.get("prize_pool_raw") or data.get("prize")
    prize_amount = getattr(raw, "prize_pool_amount", None)
    prize_currency = getattr(raw, "prize_currency", None) or data.get("prize_currency")
    if prize_amount is None:
        prize_amount, inferred_currency, prize_raw = parse_prize(
            str(prize_raw) if prize_raw else (raw.description or raw.title or "")
        )
        prize_currency = prize_currency or inferred_currency
    elif not isinstance(prize_amount, Decimal):
        try:
            prize_amount = Decimal(str(prize_amount))
        except (InvalidOperation, ValueError):
            prize_amount = None

    team_min = getattr(raw, "team_size_min", None) or data.get("team_size_min")
    team_max = getattr(raw, "team_size_max", None) or data.get("team_size_max")
    if team_min is None and team_max is None:
        team_min, team_max, team_required, individual = parse_team_size(blob)
    else:
        team_required = bool(data.get("team_required", False))
        individual = bool(data.get("individual_allowed", True))

    tags = list(getattr(raw, "tags", None) or data.get("tags") or data.get("themes") or [])
    tags = [str(t).strip()[:80] for t in tags if str(t).strip()][:20]
    tracks = list(getattr(raw, "tracks", None) or data.get("tracks") or [])
    tracks = [str(t).strip()[:80] for t in tracks if str(t).strip()][:20]

    event_type = str(data.get("event_type") or "").lower()
    opp_type = raw.opportunity_type or OpportunityType.HACKATHON
    if "challenge" in event_type and opp_type == OpportunityType.HACKATHON:
        opp_type = OpportunityType.CHALLENGE

    phase = derive_hackathon_phase(
        registration_open_at=reg_open,
        registration_deadline=registration_deadline if isinstance(registration_deadline, datetime) else None,
        start_at=start_at,
        end_at=end_at,
        submission_deadline=submission,
        fallback_deadline=raw.deadline,
        now=now,
    )

    return HackathonDetailsPayload(
        short_description=description[:500] if description else None,
        registration_url=(raw.application_url or "")[:500] or None,
        website_url=(raw.source_url or raw.application_url or "")[:500] or None,
        registration_open_at=reg_open,
        registration_deadline=registration_deadline if isinstance(registration_deadline, datetime) else None,
        start_at=start_at,
        end_at=end_at,
        submission_deadline=submission,
        announcement_at=None,
        event_format=event_format,
        prize_pool_amount=prize_amount,
        prize_currency=(str(prize_currency)[:8] if prize_currency else None),
        prize_pool_raw=(str(prize_raw)[:255] if prize_raw else None),
        team_size_min=int(team_min) if team_min is not None else None,
        team_size_max=int(team_max) if team_max is not None else None,
        team_required=bool(team_required) if team_min is not None else False,
        individual_allowed=bool(individual) if team_min is not None else True,
        tags=tags,
        tracks=tracks,
        technology_focus=str(data.get("technology_focus") or "")[:255] or None,
        derived_phase=phase.value,
        opportunity_type=opp_type,
    )
