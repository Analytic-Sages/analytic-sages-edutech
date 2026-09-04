from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.opportunity import EmploymentType, OpportunitySourceTrustLevel, OpportunityType, WorkplaceType
from app.services.opportunity_career_tracks import match_career_tracks
from app.services.opportunity_normalize import (
    LocationScope,
    infer_employment_type,
    infer_workplace_and_scope,
)
from app.services.opportunity_sources.base import RawOpportunity

RELEVANCE_REJECT_BELOW = 40
RELEVANCE_REVIEW_BELOW = 60
RELEVANCE_HIGH_AT = 80

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

TYPE_TITLE_PATTERNS: list[tuple[OpportunityType, str]] = [
    (OpportunityType.HACKATHON, r"\b(?:hackathons?|hack\s*week|buildathon|codefest)\b"),
    (OpportunityType.CHALLENGE, r"\b(?:builder\s+)?challenges?\b|\barena\b"),
    (OpportunityType.FELLOWSHIP, r"\bfellowships?\b"),
    (OpportunityType.BOUNTY, r"\bbount(?:y|ies)\b"),
    (OpportunityType.GRANT, r"\b(?:ecosystem\s+)?grants?\b|\brfps?\b"),
    (OpportunityType.INTERNSHIP, r"\binternships?\b|\binterns?\b|\buniversity\s+grad\b|\bnew\s+grad\b"),
    (
        OpportunityType.RESEARCH,
        r"\bresearch(?:er)?\s+(?:engineer|scientist|intern|fellow|associate)s?\b|\bpostdocs?\b|\bphd\b",
    ),
]
# Description-only patterns intentionally omit hackathon — job posts often mention
# "hackathon experience" without being a hackathon listing.
TYPE_DESCRIPTION_PATTERNS: list[tuple[OpportunityType, str]] = [
    (OpportunityType.FELLOWSHIP, r"\bfellowships?\b"),
    (OpportunityType.BOUNTY, r"\bbug\s+bount(?:y|ies)\b|\bbount(?:y|ies)\b"),
    (OpportunityType.GRANT, r"\bgrant\s+program\b|\becosystem\s+grants?\b|\brequest\s+for\s+proposals\b"),
    (OpportunityType.INTERNSHIP, r"\binternships?\b|\binterns?\b"),
    (
        OpportunityType.RESEARCH,
        r"\bresearch\s+(?:engineer|scientist|intern|fellow|associate)s?\b|\bpostdocs?\b",
    ),
]

JOB_SHAPED_TITLE_RE = re.compile(
    r"\b(?:senior|staff|principal|lead|junior)?\s*"
    r"(?:software|backend|frontend|full[\s-]?stack|data|ml|machine learning|devops|"
    r"security|product|solutions)?\s*"
    r"(?:engineer|developer|scientist|analyst|manager|director|recruiter|designer)s?\b",
    re.I,
)


@dataclass
class RelevanceResult:
    score: Decimal
    breakdown: dict[str, float] = field(default_factory=dict)
    career_path_slugs: list[str] = field(default_factory=list)
    skill_slugs: list[str] = field(default_factory=list)
    opportunity_type: OpportunityType = OpportunityType.JOB
    workplace_type: WorkplaceType = WorkplaceType.REMOTE
    region: str | None = None
    location_scope: LocationScope = LocationScope.UNKNOWN
    employment_type: EmploymentType | None = None
    match_reasons: list[str] = field(default_factory=list)
    matched_career_tracks: list[str] = field(default_factory=list)


def infer_opportunity_type(raw: RawOpportunity) -> OpportunityType:
    if raw.opportunity_type in {OpportunityType.HACKATHON, OpportunityType.CHALLENGE}:
        # Explicit connector type wins unless the title is clearly a job role.
        if JOB_SHAPED_TITLE_RE.search(raw.title or "") and not re.search(
            r"\bhackathons?\b", raw.title or "", re.I
        ):
            return OpportunityType.JOB
        return raw.opportunity_type
    if raw.opportunity_type == OpportunityType.BOUNTY:
        return OpportunityType.BOUNTY
    if raw.opportunity_type and raw.opportunity_type not in {OpportunityType.OTHER, OpportunityType.JOB}:
        return raw.opportunity_type

    title = (raw.title or "").lower()
    description = (raw.description or "").lower()
    # Jobs mentioning hackathons must stay jobs
    if JOB_SHAPED_TITLE_RE.search(raw.title or "") and not re.search(r"\bhackathons?\b", title):
        for opportunity_type, pattern in TYPE_TITLE_PATTERNS:
            if opportunity_type in {OpportunityType.HACKATHON, OpportunityType.CHALLENGE}:
                continue
            if re.search(pattern, title):
                return opportunity_type
        return OpportunityType.JOB

    for opportunity_type, pattern in TYPE_TITLE_PATTERNS:
        if re.search(pattern, title):
            return opportunity_type
    for opportunity_type, pattern in TYPE_DESCRIPTION_PATTERNS:
        if re.search(pattern, description):
            return opportunity_type
    return raw.opportunity_type or OpportunityType.JOB


def infer_workplace(raw: RawOpportunity) -> WorkplaceType:
    workplace, _, _, _ = infer_workplace_and_scope(
        location=raw.location or "",
        title=raw.title or "",
        description=raw.description or "",
        explicit_workplace=raw.workplace_type,
    )
    return workplace


def infer_region(raw: RawOpportunity) -> str | None:
    _, _, _, region = infer_workplace_and_scope(
        location=raw.location or "",
        title=raw.title or "",
        description=raw.description or "",
        explicit_workplace=raw.workplace_type,
    )
    return region


def score_job_relevance(
    raw: RawOpportunity,
    trust_level: OpportunitySourceTrustLevel | str,
    *,
    now: datetime | None = None,
    opportunity_type: OpportunityType | None = None,
) -> RelevanceResult:
    title = raw.title or ""
    description = raw.description or ""
    requirements = raw.requirements or ""
    blob = f"{title} {description} {requirements} {raw.location or ''}".lower()
    reasons: list[str] = []

    tracks = match_career_tracks(title=title, description=description, requirements=requirements)
    title_score = 0.0
    for match in tracks.matches:
        if match.title_hit:
            title_score = max(title_score, 50.0)
            reasons.append(f"Exact role match: {match.label}")
            break
    if title_score == 0 and tracks.matches:
        title_score = 25.0
        reasons.append(f"Partial career-track match: {tracks.matches[0].label}")

    skill_score = 0.0
    skill_slugs: list[str] = []
    for slug, keywords in SKILL_KEYWORDS.items():
        if any(keyword in blob for keyword in keywords):
            skill_slugs.append(slug)
    # Also count track skill hits
    track_skills = sorted({s for m in tracks.matches for s in m.skill_hits})
    for skill in track_skills[:6]:
        bump = 20.0 if skill_score == 0 else 10.0
        skill_score = min(40.0, skill_score + bump)
        reasons.append(f"Skill match: {skill}")
    if not track_skills and skill_slugs:
        skill_score = min(30.0, len(skill_slugs) * 10.0)
        for slug in skill_slugs[:3]:
            reasons.append(f"Skill match: {slug}")

    keyword_score = min(20.0, sum(len(m.keyword_hits) for m in tracks.matches) * 5.0)
    for match in tracks.matches[:2]:
        for kw in match.keyword_hits[:2]:
            reasons.append(f"Keyword: {kw}")

    trust_value = trust_level.value if hasattr(trust_level, "value") else str(trust_level)
    trust_score = {"high": 10.0, "medium": 5.0, "low": 0.0}.get(trust_value, 5.0)
    if trust_score >= 10:
        reasons.append("High-trust source")
    elif trust_score >= 5:
        reasons.append("Medium-trust source")

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

    negative = 0.0
    if tracks.strong_negative_title:
        negative = 50.0
        reasons.append(f"Low-priority role title: {tracks.negative_hits[0]}")
    elif tracks.negative_hits:
        negative = min(25.0, len(tracks.negative_hits) * 10.0)
        reasons.append(f"Negative keyword: {tracks.negative_hits[0]}")

    total = max(
        0.0,
        min(
            100.0,
            title_score + skill_score + keyword_score + trust_score + freshness + completeness - negative,
        ),
    )

    workplace, scope, _, region = infer_workplace_and_scope(
        location=raw.location or "",
        title=title,
        description=description,
        explicit_workplace=raw.workplace_type,
    )
    employment = infer_employment_type(f"{title} {raw.location or ''} {description[:2000]}")

    return RelevanceResult(
        score=Decimal(str(round(total, 2))),
        breakdown={
            "title": title_score,
            "skills": skill_score,
            "keywords": keyword_score,
            "source_trust": trust_score,
            "freshness": freshness,
            "completeness": completeness,
            "negative": -negative,
        },
        career_path_slugs=tracks.seed_slugs,
        skill_slugs=skill_slugs or [s.replace(" ", "-") for s in track_skills[:8]],
        opportunity_type=opportunity_type or infer_opportunity_type(raw),
        workplace_type=workplace,
        region=region,
        location_scope=scope,
        employment_type=employment,
        match_reasons=reasons[:12],
        matched_career_tracks=[m.track_key for m in tracks.matches],
    )


def score_relevance(
    raw: RawOpportunity,
    trust_level: OpportunitySourceTrustLevel | str,
    *,
    now: datetime | None = None,
) -> RelevanceResult:
    inferred = infer_opportunity_type(raw)
    if inferred in {OpportunityType.HACKATHON, OpportunityType.CHALLENGE}:
        from app.services.hackathon_relevance import score_hackathon_relevance

        return score_hackathon_relevance(raw, trust_level, now=now)
    if inferred == OpportunityType.BOUNTY or raw.opportunity_type == OpportunityType.BOUNTY:
        from app.services.bounty_relevance import score_bounty_relevance

        return score_bounty_relevance(raw, trust_level, now=now)
    return score_job_relevance(raw, trust_level, now=now, opportunity_type=inferred)


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
