"""Relevance scoring tuned for bounties / quests (not jobs or hackathons)."""

from __future__ import annotations

import re
from decimal import Decimal

from app.models.opportunity import OpportunitySourceTrustLevel, OpportunityType
from app.services.bounty_normalize import infer_bounty_category
from app.services.opportunity_relevance import RelevanceResult, infer_workplace, score_job_relevance
from app.services.opportunity_sources.base import RawOpportunity

BOUNTY_FOCUS: dict[str, tuple[str, ...]] = {
    "security": ("bug bounty", "security", "immunefi", "audit", "vulnerability"),
    "defi": ("defi", "amm", "lending"),
    "content": ("content", "thread", "writing", "video"),
    "development": ("sdk", "integration", "build", "developer"),
    "solana": ("solana", "svm"),
    "ethereum": ("ethereum", "evm", "solidity"),
    "data": ("data", "analytics", "dune", "indexing"),
}

JOB_TITLE_RE = re.compile(
    r"\b(?:senior|staff|principal|lead|junior)?\s*"
    r"(?:software|backend|frontend|full[\s-]?stack|data|ml|machine learning|devops|"
    r"security|product|solutions)?\s*"
    r"(?:engineer|developer|scientist|analyst|manager|director|recruiter|designer)s?\b",
    re.I,
)
HACKATHON_TITLE_RE = re.compile(r"\b(?:hackathons?|buildathon|codefest|ethglobal)\b", re.I)
BOUNTY_TITLE_RE = re.compile(
    r"\b(?:bug\s+)?bount(?:y|ies)\b|\breward\s+program\b|\bquests?\b|\bearn\b",
    re.I,
)


def classify_bounty_type(raw: RawOpportunity) -> OpportunityType:
    if raw.opportunity_type == OpportunityType.BOUNTY:
        if JOB_TITLE_RE.search(raw.title or "") and not BOUNTY_TITLE_RE.search(raw.title or ""):
            return OpportunityType.JOB
        if HACKATHON_TITLE_RE.search(raw.title or ""):
            return OpportunityType.HACKATHON
        return OpportunityType.BOUNTY
    if raw.opportunity_type in {OpportunityType.HACKATHON, OpportunityType.CHALLENGE}:
        return raw.opportunity_type
    if raw.opportunity_type and raw.opportunity_type not in {OpportunityType.OTHER, OpportunityType.JOB}:
        return raw.opportunity_type

    title = raw.title or ""
    if HACKATHON_TITLE_RE.search(title):
        return OpportunityType.HACKATHON
    if JOB_TITLE_RE.search(title) and not BOUNTY_TITLE_RE.search(title):
        return OpportunityType.JOB
    if BOUNTY_TITLE_RE.search(title):
        return OpportunityType.BOUNTY
    return raw.opportunity_type or OpportunityType.JOB


def score_bounty_relevance(
    raw: RawOpportunity,
    trust_level: OpportunitySourceTrustLevel | str,
    *,
    now=None,
) -> RelevanceResult:
    opp_type = classify_bounty_type(raw)
    if opp_type != OpportunityType.BOUNTY:
        return score_job_relevance(raw, trust_level, now=now, opportunity_type=opp_type)

    title = (raw.title or "").lower()
    description = (raw.description or "").lower()
    blob = f"{title} {description}"
    reasons: list[str] = []

    focus_score = 0.0
    tracks: list[str] = []
    for key, keywords in BOUNTY_FOCUS.items():
        if any(kw in blob for kw in keywords):
            tracks.append(key)
            focus_score = min(40.0, focus_score + (15.0 if focus_score == 0 else 8.0))
            reasons.append(f"Focus: {key}")

    title_score = 35.0 if BOUNTY_TITLE_RE.search(title) else 18.0
    if title_score >= 35:
        reasons.append("Bounty / earn listing title")

    trust_value = trust_level.value if hasattr(trust_level, "value") else str(trust_level)
    trust_score = {"high": 15.0, "medium": 8.0, "low": 0.0}.get(trust_value, 8.0)
    if trust_score >= 15:
        reasons.append("High-trust earn source")

    completeness = 0.0
    if raw.title:
        completeness += 2.0
    if raw.application_url:
        completeness += 3.0
    if raw.deadline or getattr(raw, "bounty_deadline", None):
        completeness += 3.0
        reasons.append("Has deadline")
    if raw.description and len(raw.description) >= 40:
        completeness += 2.0
    if getattr(raw, "reward_amount", None) is not None or "reward" in blob:
        completeness += 3.0
        reasons.append("Has reward info")

    category = infer_bounty_category(raw.title or "", raw.description or "")
    reasons.append(f"Category: {category.value}")

    web3_boost = 10.0 if any(
        token in blob
        for token in ("web3", "blockchain", "solana", "ethereum", "defi", "onchain", "crypto")
    ) else 0.0
    if web3_boost:
        reasons.append("Web3 earn listing")

    negative = 0.0
    if JOB_TITLE_RE.search(raw.title or "") and not BOUNTY_TITLE_RE.search(raw.title or ""):
        negative = 40.0
        reasons.append("Looks like a job posting, not a bounty")
    if HACKATHON_TITLE_RE.search(raw.title or ""):
        negative = max(negative, 35.0)
        reasons.append("Looks like a hackathon, not a bounty")

    total = max(
        0.0,
        min(100.0, title_score + focus_score + trust_score + completeness + web3_boost - negative),
    )

    return RelevanceResult(
        score=Decimal(str(round(total, 2))),
        breakdown={
            "title": title_score,
            "focus": focus_score,
            "source_trust": trust_score,
            "completeness": completeness,
            "web3": web3_boost,
            "negative": -negative,
        },
        career_path_slugs=["blockchain-data", "smart-contracts"][:2] if web3_boost else [],
        skill_slugs=tracks[:6],
        opportunity_type=OpportunityType.BOUNTY,
        workplace_type=infer_workplace(raw),
        match_reasons=reasons[:12],
        matched_career_tracks=tracks[:8],
    )
