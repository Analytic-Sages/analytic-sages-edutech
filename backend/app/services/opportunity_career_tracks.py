"""Central career-track definitions for opportunity matching.

Maps to seeded career_paths.slug values where possible.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Slugs align with seed_opportunities.CAREER_PATHS
CAREER_TRACKS: dict[str, dict] = {
    "onchain-data-analytics": {
        "label": "Blockchain & Onchain Data",
        "title_exact": (
            "blockchain data engineer",
            "onchain data engineer",
            "crypto data engineer",
            "blockchain data analyst",
            "onchain data analyst",
            "blockchain analytics",
            "onchain analytics",
            "crypto analytics",
            "analytics engineer",
        ),
        "keywords": (
            "blockchain data",
            "onchain data",
            "on-chain data",
            "crypto data",
            "blockchain analytics",
            "onchain analytics",
            "on-chain analytics",
            "dune",
            "flipside",
            "the graph",
            "subgraph",
            "token analytics",
            "protocol analytics",
        ),
        "skills": (
            "sql",
            "python",
            "dune",
            "flipside",
            "clickhouse",
            "postgresql",
            "dbt",
            "spark",
            "kafka",
            "etl",
            "elt",
            "the graph",
        ),
    },
    "blockchain-data-engineering": {
        "label": "Data Engineering & Analytics",
        "title_exact": (
            "data engineer",
            "analytics engineer",
            "data analyst",
            "data scientist",
            "data platform engineer",
            "etl engineer",
            "bi engineer",
        ),
        "keywords": (
            "data engineer",
            "data engineering",
            "analytics engineer",
            "data platform",
            "etl",
            "elt",
            "data pipeline",
        ),
        "skills": (
            "python",
            "sql",
            "dbt",
            "airflow",
            "spark",
            "kafka",
            "snowflake",
            "bigquery",
            "postgresql",
            "clickhouse",
        ),
    },
    "research-intelligence": {
        "label": "Research & Intelligence",
        "title_exact": (
            "research analyst",
            "crypto research analyst",
            "protocol researcher",
            "onchain researcher",
            "blockchain researcher",
            "market research analyst",
            "investment research analyst",
            "intelligence analyst",
        ),
        "keywords": (
            "research analyst",
            "protocol research",
            "onchain research",
            "market research",
            "investment research",
            "intelligence analyst",
        ),
        "skills": ("research", "sql", "python", "onchain"),
        # Not in seed — will map to closest or create soft match only in reasons
        "seed_slug": None,
    },
    "quantitative-trading": {
        "label": "Quantitative & Financial Markets",
        "title_exact": (
            "quantitative analyst",
            "quantitative researcher",
            "quant researcher",
            "quant developer",
            "quant trader",
            "systematic researcher",
            "trading analyst",
            "market analyst",
        ),
        "keywords": (
            "quantitative",
            "quant ",
            "quant-",
            "systematic trading",
            "market microstructure",
            "trading analyst",
        ),
        "skills": (
            "python",
            "statistics",
            "probability",
            "time series",
            "machine learning",
            "c++",
            "rust",
        ),
    },
    "blockchain-investigative-forensic-analytics": {
        "label": "Blockchain Investigation & Intelligence",
        "title_exact": (
            "blockchain forensic investigator",
            "blockchain investigator",
            "crypto investigator",
            "onchain investigator",
            "investigative analyst",
            "financial crime analyst",
            "crypto intelligence analyst",
        ),
        "keywords": (
            "blockchain forensic",
            "crypto investigator",
            "onchain investigator",
            "transaction tracing",
            "blockchain intelligence",
            "financial crime",
            "aml",
            "osint",
        ),
        "skills": (
            "transaction tracing",
            "blockchain intelligence",
            "graph analysis",
            "aml",
            "kyc",
            "osint",
        ),
    },
    "applied-ai": {
        "label": "AI & Machine Learning",
        "title_exact": (
            "machine learning engineer",
            "ai engineer",
            "applied ai engineer",
            "research engineer",
            "llm engineer",
            "ai infrastructure engineer",
            "ml researcher",
            "data scientist",
        ),
        "keywords": (
            "machine learning",
            "ml engineer",
            "applied ai",
            "llm engineer",
            "ai infrastructure",
            "deep learning",
        ),
        "skills": (
            "pytorch",
            "tensorflow",
            "scikit-learn",
            "llm",
            "rag",
            "vector database",
        ),
    },
    "agentic-systems": {
        "label": "AI Agents & Agent Engineering",
        "title_exact": (
            "ai agent engineer",
            "agent engineer",
            "ai agents engineer",
            "agentic ai engineer",
            "agentic systems engineer",
            "multi-agent systems engineer",
            "llm agent engineer",
            "autonomous systems engineer",
        ),
        "keywords": (
            "ai agent",
            "agentic",
            "multi-agent",
            "llm agent",
            "agent orchestration",
            "tool calling",
            "function calling",
            "mcp",
            "model context protocol",
        ),
        "skills": (
            "langchain",
            "langgraph",
            "crewai",
            "autogen",
            "mcp",
            "rag",
            "vector database",
        ),
    },
    "ai-automation": {
        "label": "AI Automation Engineering",
        "title_exact": (
            "ai automation engineer",
            "automation engineer",
            "ai workflow engineer",
            "intelligent automation engineer",
            "workflow automation engineer",
            "automation developer",
            "ai solutions engineer",
        ),
        "keywords": (
            "ai automation",
            "workflow automation",
            "intelligent automation",
            "rpa",
            "n8n",
            "zapier",
            "make.com",
        ),
        "skills": (
            "n8n",
            "make",
            "zapier",
            "python",
            "fastapi",
            "webhooks",
            "rpa",
            "llm api",
        ),
    },
}

# Seed slug aliases for tracks not yet in DB under the same key
TRACK_TO_SEED_SLUG: dict[str, str] = {
    "onchain-data-analytics": "onchain-data-analytics",
    "blockchain-data-engineering": "blockchain-data-engineering",
    "research-intelligence": "onchain-data-analytics",  # closest until dedicated path seeded
    "quantitative-trading": "quantitative-trading",
    "blockchain-investigative-forensic-analytics": "blockchain-investigative-forensic-analytics",
    "applied-ai": "applied-ai",
    "agentic-systems": "agentic-systems",
    "ai-automation": "ai-automation",
    "machine-learning-for-blockchain": "machine-learning-for-blockchain",
}

NEGATIVE_TITLE_PATTERNS = (
    "smart contract auditor",
    "solidity auditor",
    "security auditor",
    "legal counsel",
    "community manager",
    "community lead",
    "graphic designer",
    "social media manager",
    "social media",
    "nft artist",
    "marketing manager",
    "growth marketer",
    "content writer",
    "discord manager",
    "brand designer",
)

# Soft negatives — penalize but don't alone reject
NEGATIVE_KEYWORDS = (
    "auditor",
    "audit",
    "marketing",
    "community manager",
    "graphic designer",
    "social media",
    "nft artist",
    "influencer",
    "brand designer",
)


@dataclass
class CareerTrackMatch:
    track_key: str
    seed_slug: str
    label: str
    title_hit: bool = False
    keyword_hits: list[str] = field(default_factory=list)
    skill_hits: list[str] = field(default_factory=list)


@dataclass
class CareerTrackResult:
    matches: list[CareerTrackMatch] = field(default_factory=list)
    negative_hits: list[str] = field(default_factory=list)
    strong_negative_title: bool = False

    @property
    def seed_slugs(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for match in self.matches:
            if match.seed_slug not in seen:
                seen.add(match.seed_slug)
                out.append(match.seed_slug)
        return out

    @property
    def track_keys(self) -> list[str]:
        return [m.track_key for m in self.matches]


def match_career_tracks(*, title: str, description: str, requirements: str = "") -> CareerTrackResult:
    title_l = (title or "").lower()
    blob = f"{title} {description} {requirements}".lower()
    result = CareerTrackResult()

    for pattern in NEGATIVE_TITLE_PATTERNS:
        if pattern in title_l:
            result.strong_negative_title = True
            result.negative_hits.append(pattern)
            break
    for keyword in NEGATIVE_KEYWORDS:
        if keyword in blob and keyword not in result.negative_hits:
            result.negative_hits.append(keyword)

    for track_key, spec in CAREER_TRACKS.items():
        title_hit = any(exact in title_l for exact in spec["title_exact"])
        keyword_hits = [kw for kw in spec["keywords"] if kw in blob]
        skill_hits = [sk for sk in spec["skills"] if sk in blob]
        if not title_hit and not keyword_hits and not skill_hits:
            continue
        # Require more than a lone weak skill for non-title matches
        if not title_hit and not keyword_hits and len(skill_hits) < 2:
            continue
        result.matches.append(
            CareerTrackMatch(
                track_key=track_key,
                seed_slug=TRACK_TO_SEED_SLUG.get(track_key, track_key),
                label=spec["label"],
                title_hit=title_hit,
                keyword_hits=keyword_hits[:5],
                skill_hits=skill_hits[:5],
            )
        )

    # Prefer title hits first
    result.matches.sort(key=lambda m: (not m.title_hit, -len(m.keyword_hits) - len(m.skill_hits)))
    return result
