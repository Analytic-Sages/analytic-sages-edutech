from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.opportunity import OpportunitySourceTrustLevel, OpportunityType, WorkplaceType
from app.services.opportunity_sources.base import RawOpportunity

HIGH_KEYWORDS = (
    "onchain",
    "on-chain",
    "blockchain analytics",
    "crypto data",
    "web3",
    "data engineer",
    "data engineering",
    "quantitative",
    "forensic",
    "forensics",
    "agentic",
    "defi",
    "dune",
    "solidity",
    "etl",
    "machine learning",
    "llm",
    "spark",
    "sql",
    "python",
    "protocol analytics",
    "token analytics",
    "blockchain",
    "crypto",
)

CAREER_PATH_KEYWORDS: dict[str, tuple[str, ...]] = {
    "onchain-data-analytics": ("onchain", "on-chain", "dune", "blockchain analytics", "crypto data", "token analytic"),
    "blockchain-data-engineering": ("data engineer", "data engineering", "etl", "spark", "pipeline"),
    "applied-ai": ("applied ai", "machine learning", "ml engineer", "model"),
    "agentic-systems": ("agentic", "ai agent", "autonomous agent"),
    "ai-automation": ("automation", "orchestrat", "workflow"),
    "quantitative-trading": ("quantitative", "quant ", "trading", "market making"),
    "blockchain-investigative-forensic-analytics": ("forensic", "investigat", "aml", "compliance", "trace"),
    "machine-learning-for-blockchain": ("machine learning", "ml for blockchain", "graph neural"),
}

SKILL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "sql": ("sql",),
    "python": ("python",),
    "dune": ("dune",),
    "blockchain": ("blockchain", "web3", "onchain"),
    "solidity": ("solidity",),
    "etl": ("etl",),
    "data-engineering": ("data engineer", "data engineering"),
    "machine-learning": ("machine learning", " ml "),
    "statistics": ("statistic",),
    "spark": ("spark",),
    "llm": ("llm", "large language"),
    "onchain-analytics": ("onchain", "on-chain analytic"),
}

# Title-first patterns use word boundaries so "intern" does not match "internal".
TYPE_TITLE_PATTERNS: list[tuple[OpportunityType, str]] = [
    (OpportunityType.HACKATHON, r"\bhackathons?\b"),
    (OpportunityType.FELLOWSHIP, r"\bfellowships?\b"),
    (OpportunityType.BOUNTY, r"\bbount(?:y|ies)\b"),
    (OpportunityType.GRANT, r"\b(?:ecosystem\s+)?grants?\b|\brfps?\b"),
    (OpportunityType.INTERNSHIP, r"\binternships?\b|\binterns?\b|\buniversity\s+grad\b|\bnew\s+grad\b"),
    (OpportunityType.RESEARCH, r"\bresearch(?:er)?\s+(?:engineer|scientist|intern|fellow|associate)s?\b|\bpostdocs?\b|\bphd\b"),
]
TYPE_DESCRIPTION_PATTERNS: list[tuple[OpportunityType, str]] = [
    (OpportunityType.HACKATHON, r"\bhackathons?\b"),
    (OpportunityType.FELLOWSHIP, r"\bfellowships?\b"),
    (OpportunityType.BOUNTY, r"\bbug\s+bount(?:y|ies)\b|\bbount(?:y|ies)\b"),
    (OpportunityType.GRANT, r"\bgrant\s+program\b|\becosystem\s+grants?\b|\brequest\s+for\s+proposals\b"),
    (OpportunityType.INTERNSHIP, r"\binternships?\b|\binterns?\b"),
    (OpportunityType.RESEARCH, r"\bresearch\s+(?:engineer|scientist|intern|fellow|associate)s?\b|\bpostdocs?\b"),
]

REGION_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("nigeria", ("nigeria", "lagos", "abuja")),
    ("africa", ("africa", "kenya", "ghana", "rwanda", "south africa")),
    ("europe", ("europe", "london", "berlin", "amsterdam", "paris", "lisbon")),
    ("north_america", ("united states", "usa", "canada", "new york", "san francisco")),
    ("asia", ("asia", "singapore", "india", "bangalore", "tokyo")),
    ("remote", ("remote", "anywhere")),
]

RELEVANCE_REJECT_BELOW = 40
RELEVANCE_REVIEW_BELOW = 60
RELEVANCE_HIGH_AT = 80


@dataclass
class RelevanceResult:
    score: Decimal
    breakdown: dict[str, float] = field(default_factory=dict)
    career_path_slugs: list[str] = field(default_factory=list)
    skill_slugs: list[str] = field(default_factory=list)
    opportunity_type: OpportunityType = OpportunityType.JOB
    workplace_type: WorkplaceType = WorkplaceType.REMOTE
    region: str | None = None


def _blob(raw: RawOpportunity) -> str:
    return " ".join(
        part for part in (raw.title, raw.organization_name, raw.description, raw.requirements, raw.location) if part
    ).lower()


def _count_keywords(text: str, keywords: tuple[str, ...]) -> int:
    hits = 0
    for keyword in keywords:
        if keyword in text:
            hits += 1
    return hits


def infer_opportunity_type(raw: RawOpportunity) -> OpportunityType:
    if raw.opportunity_type:
        return raw.opportunity_type
    title = (raw.title or "").lower()
    description = (raw.description or "").lower()
    for opportunity_type, pattern in TYPE_TITLE_PATTERNS:
        if re.search(pattern, title):
            return opportunity_type
    for opportunity_type, pattern in TYPE_DESCRIPTION_PATTERNS:
        if re.search(pattern, description):
            return opportunity_type
    return OpportunityType.JOB


def infer_workplace(raw: RawOpportunity) -> WorkplaceType:
    if raw.workplace_type:
        return raw.workplace_type
    text = f"{raw.title} {raw.location} {raw.description}".lower()
    if "hybrid" in text:
        return WorkplaceType.HYBRID
    if any(token in text for token in ("onsite", "on-site", "in office", "in-office")):
        return WorkplaceType.ONSITE
    return WorkplaceType.REMOTE


def infer_region(raw: RawOpportunity) -> str | None:
    text = f"{raw.location} {raw.title} {raw.description}".lower()
    for region, keywords in REGION_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return region
    return "global" if raw.location else "remote"


def score_relevance(
    raw: RawOpportunity,
    trust_level: OpportunitySourceTrustLevel | str,
    *,
    now: datetime | None = None,
) -> RelevanceResult:
    text = _blob(raw)
    keyword_hits = _count_keywords(text, HIGH_KEYWORDS)
    keywords_score = min(40.0, keyword_hits * 8.0)

    career_slugs = [
        slug for slug, keywords in CAREER_PATH_KEYWORDS.items() if any(keyword in text for keyword in keywords)
    ]
    career_score = min(25.0, len(career_slugs) * 10.0)

    skill_slugs = [
        slug for slug, keywords in SKILL_KEYWORDS.items() if any(keyword in text for keyword in keywords)
    ]

    trust_value = trust_level.value if hasattr(trust_level, "value") else str(trust_level)
    trust_score = {"high": 20.0, "medium": 12.0, "low": 5.0}.get(trust_value, 12.0)

    current = now or datetime.now(UTC)
    posted = raw.posted_at
    if posted is None:
        freshness = 5.0
    else:
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=UTC)
        age = current - posted.astimezone(UTC)
        if age <= timedelta(days=14):
            freshness = 10.0
        elif age <= timedelta(days=30):
            freshness = 6.0
        elif age <= timedelta(days=90):
            freshness = 3.0
        else:
            freshness = 1.0

    completeness = 0.0
    if raw.title:
        completeness += 1.0
    if raw.organization_name:
        completeness += 1.0
    if raw.application_url:
        completeness += 1.0
    if len(raw.description) >= 80:
        completeness += 2.0
    elif raw.description:
        completeness += 1.0

    total = min(100.0, keywords_score + career_score + trust_score + freshness + completeness)
    return RelevanceResult(
        score=Decimal(str(round(total, 2))),
        breakdown={
            "keywords": keywords_score,
            "career_paths": career_score,
            "source_trust": trust_score,
            "freshness": freshness,
            "completeness": completeness,
        },
        career_path_slugs=career_slugs,
        skill_slugs=skill_slugs,
        opportunity_type=infer_opportunity_type(raw),
        workplace_type=infer_workplace(raw),
        region=infer_region(raw),
    )


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
