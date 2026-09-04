"""Normalize bounty-specific fields from RawOpportunity payloads."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.models.opportunity import BountyCategory, OpportunityType
from app.services.bounty_dates import BountyPhase, derive_bounty_phase
from app.services.opportunity_sources.base import RawOpportunity

REWARD_RE = re.compile(
    r"(?:reward|prize|up\s+to)?\s*(?:\$|usd\s*)?\s*([\d][\d,]*(?:\.\d+)?)\s*"
    r"(k|m|million|thousand)?\s*(usdc|usdt|usd|sol|eth|\$)?",
    re.I,
)
CATEGORY_PATTERNS: list[tuple[BountyCategory, str]] = [
    (BountyCategory.BUG, r"\bbug\s+bount"),
    (BountyCategory.SECURITY, r"\b(?:security|immunefi|audit)\b"),
    (BountyCategory.CONTENT, r"\b(?:content|writing|thread|article|video)\b"),
    (BountyCategory.DESIGN, r"\b(?:design|ui|ux|brand)\b"),
    (BountyCategory.RESEARCH, r"\b(?:research|analysis|report)\b"),
    (BountyCategory.QUEST, r"\b(?:quest|mission|campaign)\b"),
    (BountyCategory.DEVELOPMENT, r"\b(?:dev|developer|build|code|sdk|integration)\b"),
]


@dataclass
class BountyDetailsPayload:
    short_description: str | None = None
    listing_url: str | None = None
    reward_amount: Decimal | None = None
    reward_token: str | None = None
    reward_currency: str | None = None
    reward_raw: str | None = None
    reward_min: Decimal | None = None
    reward_max: Decimal | None = None
    category: BountyCategory = BountyCategory.UNKNOWN
    opens_at: datetime | None = None
    deadline: datetime | None = None
    winners_announced: bool = False
    skills: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    chain_focus: str | None = None
    derived_phase: str = BountyPhase.UNKNOWN.value


def infer_bounty_category(title: str, description: str = "", listing_type: str = "") -> BountyCategory:
    blob = f"{listing_type} {title} {description}".lower()
    for category, pattern in CATEGORY_PATTERNS:
        if re.search(pattern, blob):
            return category
    if "bounty" in blob:
        return BountyCategory.OTHER
    return BountyCategory.UNKNOWN


def parse_reward(text: str | None) -> tuple[Decimal | None, str | None, str | None]:
    if not text:
        return None, None, None
    cleaned = str(text).strip()[:255]
    match = REWARD_RE.search(cleaned.replace(",", ""))
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
    token = (match.group(3) or "").upper().replace("$", "USD") or None
    currency = "USD" if token in {None, "USD", "USDC", "USDT"} or "$" in cleaned else None
    return amount, token, cleaned


def normalize_bounty_details(
    raw: RawOpportunity,
    *,
    now: datetime | None = None,
) -> BountyDetailsPayload:
    data: dict[str, Any] = raw.raw_data if isinstance(raw.raw_data, dict) else {}
    description = (raw.description or "")[:500]
    listing_type = str(data.get("listing_type") or data.get("type") or "")

    deadline = getattr(raw, "bounty_deadline", None) or data.get("deadline") or raw.deadline
    if not isinstance(deadline, datetime):
        deadline = raw.deadline if isinstance(raw.deadline, datetime) else None

    opens_at = getattr(raw, "opens_at", None) or data.get("opens_at")
    if not isinstance(opens_at, datetime):
        opens_at = None

    winners = bool(
        getattr(raw, "winners_announced", None)
        if getattr(raw, "winners_announced", None) is not None
        else data.get("isWinnersAnnounced") or data.get("winners_announced") or False
    )

    reward_amount = getattr(raw, "reward_amount", None)
    reward_token = getattr(raw, "reward_token", None) or data.get("token") or data.get("reward_token")
    reward_currency = getattr(raw, "reward_currency", None) or data.get("reward_currency")
    reward_raw = getattr(raw, "reward_raw", None) or data.get("reward_raw")
    if reward_amount is None and data.get("rewardAmount") not in (None, ""):
        try:
            reward_amount = Decimal(str(data.get("rewardAmount")))
        except (InvalidOperation, ValueError):
            reward_amount = None
    if reward_amount is None:
        reward_amount, inferred_token, reward_raw = parse_reward(
            str(reward_raw) if reward_raw else (raw.description or raw.title or "")
        )
        reward_token = reward_token or inferred_token
    elif not isinstance(reward_amount, Decimal):
        try:
            reward_amount = Decimal(str(reward_amount))
        except (InvalidOperation, ValueError):
            reward_amount = None

    if reward_raw is None and reward_amount is not None:
        reward_raw = f"{reward_amount} {reward_token or reward_currency or ''}".strip()

    category = getattr(raw, "bounty_category", None)
    if not isinstance(category, BountyCategory):
        category = infer_bounty_category(raw.title or "", raw.description or "", listing_type)

    skills = list(getattr(raw, "bounty_skills", None) or data.get("skills") or [])
    skills = [str(s).strip()[:80] for s in skills if str(s).strip()][:20]
    tags = list(getattr(raw, "tags", None) or data.get("tags") or [])
    tags = [str(t).strip()[:80] for t in tags if str(t).strip()][:20]

    chain = getattr(raw, "chain_focus", None) or data.get("chain_focus")
    if not chain:
        blob = f"{raw.title} {raw.description} {raw.organization_name}".lower()
        for name in ("solana", "ethereum", "base", "polygon", "sui", "aptos"):
            if name in blob:
                chain = name
                break

    phase = derive_bounty_phase(
        opens_at=opens_at,
        deadline=deadline,
        winners_announced=winners,
        fallback_deadline=raw.deadline,
        now=now,
    )

    return BountyDetailsPayload(
        short_description=description[:500] if description else None,
        listing_url=(raw.application_url or "")[:500] or None,
        reward_amount=reward_amount,
        reward_token=(str(reward_token)[:32] if reward_token else None),
        reward_currency=(str(reward_currency)[:8] if reward_currency else None),
        reward_raw=(str(reward_raw)[:255] if reward_raw else None),
        reward_min=None,
        reward_max=None,
        category=category,
        opens_at=opens_at,
        deadline=deadline,
        winners_announced=winners,
        skills=skills,
        tags=tags,
        chain_focus=(str(chain)[:120] if chain else None),
        derived_phase=phase.value,
    )
