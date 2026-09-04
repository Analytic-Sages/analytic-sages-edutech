"""Relevance scoring tuned for hackathons / challenges (not job titles)."""

from __future__ import annotations

import re
from decimal import Decimal

from app.models.opportunity import OpportunitySourceTrustLevel, OpportunityType
from app.services.opportunity_relevance import RelevanceResult, infer_workplace, score_job_relevance
from app.services.opportunity_sources.base import RawOpportunity

HACKATHON_FOCUS: dict[str, tuple[str, ...]] = {
    "defi": ("defi", "decentralized finance", "amm", "lending protocol"),
    "ai-agents": ("ai agent", "agents", "autonomous agent", "llm agent"),
    "onchain": ("onchain", "on-chain", "smart contract", "solidity", "rust"),
    "data": ("data", "analytics", "dune", "indexing", "subgraph"),
    "infra": ("infrastructure", "l2", "rollup", "rpc", "node"),
    "security": ("security", "audit", "zk", "zero knowledge"),
    "solana": ("solana", "svm"),
    "ethereum": ("ethereum", "eth ", "evm"),
}

JOB_TITLE_RE = re.compile(
    r"\b(?:senior|staff|principal|lead|junior)?\s*"
    r"(?:software|backend|frontend|full[\s-]?stack|data|ml|machine learning|devops|"
    r"security|product|solutions)?\s*"
    r"(?:engineer|developer|scientist|analyst|manager|director|recruiter|designer)s?\b",
    re.I,
)
BOUNTY_TITLE_RE = re.compile(r"\b(?:bug\s+)?bount(?:y|ies)\b|\breward\s+program\b", re.I)
HACKATHON_TITLE_RE = re.compile(
    r"\b(?:hackathons?|hack\s*week|buildathon|codefest|ethglobal|colosseum)\b",
    re.I,
)
CHALLENGE_TITLE_RE = re.compile(r"\b(?:challenge|arena|tournament)\b", re.I)


def is_job_shaped_title(title: str) -> bool:
    return bool(JOB_TITLE_RE.search(title or ""))


def is_bounty_shaped(title: str, description: str = "") -> bool:
    blob = f"{title} {description[:400]}"
    return bool(BOUNTY_TITLE_RE.search(blob)) and not HACKATHON_TITLE_RE.search(title or "")


def classify_event_type(raw: RawOpportunity) -> OpportunityType:
    """Stricter typing: jobs/bounties must not silently become hackathons."""
    if raw.opportunity_type in {OpportunityType.HACKATHON, OpportunityType.CHALLENGE}:
        # Connector asserted type — still block obvious job titles unless platform source
        if is_job_shaped_title(raw.title) and not HACKATHON_TITLE_RE.search(raw.title or ""):
            return OpportunityType.JOB
        return raw.opportunity_type
    if raw.opportunity_type == OpportunityType.BOUNTY:
        return OpportunityType.BOUNTY
    if raw.opportunity_type and raw.opportunity_type not in {
        OpportunityType.OTHER,
        OpportunityType.JOB,
    }:
        return raw.opportunity_type

    title = raw.title or ""
    description = raw.description or ""
    if is_bounty_shaped(title, description):
        return OpportunityType.BOUNTY
    if is_job_shaped_title(title) and not HACKATHON_TITLE_RE.search(title):
        return OpportunityType.JOB
    if HACKATHON_TITLE_RE.search(title):
        return OpportunityType.HACKATHON
    if CHALLENGE_TITLE_RE.search(title) and not is_job_shaped_title(title):
        return OpportunityType.CHALLENGE
    # Do not promote from description alone — jobs often mention "hackathon experience"
    return raw.opportunity_type or OpportunityType.JOB


def score_hackathon_relevance(
    raw: RawOpportunity,
    trust_level: OpportunitySourceTrustLevel | str,
    *,
    now=None,
) -> RelevanceResult:
    """Score builder-event relevance; falls back to job scorer for non-events."""
    opp_type = classify_event_type(raw)
    if opp_type not in {OpportunityType.HACKATHON, OpportunityType.CHALLENGE}:
        return score_job_relevance(raw, trust_level, now=now, opportunity_type=opp_type)

    title = (raw.title or "").lower()
    description = (raw.description or "").lower()
    blob = f"{title} {description} {(raw.location or '').lower()}"
    reasons: list[str] = []
    focus_score = 0.0
    tracks: list[str] = []
    for key, keywords in HACKATHON_FOCUS.items():
        if any(kw in blob for kw in keywords):
            tracks.append(key)
            focus_score = min(40.0, focus_score + (15.0 if focus_score == 0 else 8.0))
            reasons.append(f"Focus: {key}")

    if HACKATHON_TITLE_RE.search(title) or CHALLENGE_TITLE_RE.search(title):
        title_score = 35.0
        reasons.append("Hackathon / challenge title")
    else:
        title_score = 15.0

    trust_value = trust_level.value if hasattr(trust_level, "value") else str(trust_level)
    trust_score = {"high": 15.0, "medium": 8.0, "low": 0.0}.get(trust_value, 8.0)
    if trust_score >= 15:
        reasons.append("High-trust hackathon platform")

    completeness = 0.0
    if raw.title:
        completeness += 2.0
    if raw.application_url:
        completeness += 3.0
    if raw.deadline or getattr(raw, "registration_deadline", None):
        completeness += 3.0
        reasons.append("Has registration / deadline date")
    if raw.description and len(raw.description) >= 40:
        completeness += 2.0
    if raw.workplace_type is not None:
        completeness += 2.0

    web3_boost = 10.0 if any(
        token in blob
        for token in ("web3", "blockchain", "ethereum", "solana", "crypto", "onchain", "defi")
    ) else 0.0
    if web3_boost:
        reasons.append("Web3 / onchain builder event")

    negative = 0.0
    if is_job_shaped_title(raw.title):
        negative = 40.0
        reasons.append("Looks like a job posting, not a hackathon")
    if is_bounty_shaped(raw.title, raw.description):
        negative = max(negative, 30.0)
        reasons.append("Looks like a bounty, not a hackathon")

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
        opportunity_type=opp_type,
        workplace_type=infer_workplace(raw),
        match_reasons=reasons[:12],
        matched_career_tracks=tracks[:8],
    )
