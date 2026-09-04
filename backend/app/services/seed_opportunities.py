"""Seed career paths, skills, and the Manual opportunity source. No fake listings."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.opportunity import (
    CareerPath,
    OpportunitySource,
    OpportunitySourceHealth,
    OpportunitySourceRole,
    OpportunitySourceTrustLevel,
    OpportunitySourceType,
    Skill,
)

CAREER_PATHS = [
    (
        "Onchain Data Analytics",
        "onchain-data-analytics",
        "Analyze public blockchain data to understand markets, protocols, and user behavior.",
        10,
    ),
    (
        "Blockchain Data Engineering",
        "blockchain-data-engineering",
        "Build pipelines that ingest, model, and serve onchain data for analytics teams.",
        20,
    ),
    (
        "Applied AI",
        "applied-ai",
        "Apply machine learning and AI systems to real products and research problems.",
        30,
    ),
    (
        "Agentic Systems",
        "agentic-systems",
        "Design and evaluate autonomous and semi-autonomous AI agents.",
        40,
    ),
    (
        "AI Automation",
        "ai-automation",
        "Automate workflows with models, tools, and reliable orchestration.",
        50,
    ),
    (
        "Quantitative Trading",
        "quantitative-trading",
        "Research and implement data-driven trading strategies across crypto markets.",
        60,
    ),
    (
        "Blockchain Investigative / Forensic Analytics",
        "blockchain-investigative-forensic-analytics",
        "Trace funds, investigate incidents, and support compliance with onchain evidence.",
        70,
    ),
    (
        "Machine Learning for Blockchain",
        "machine-learning-for-blockchain",
        "Train and evaluate models on blockchain, market, and protocol datasets.",
        80,
    ),
]

SKILLS = [
    ("SQL", "sql", "analytics"),
    ("Python", "python", "engineering"),
    ("Dune", "dune", "tools"),
    ("Blockchain", "blockchain", "blockchain"),
    ("Solidity", "solidity", "blockchain"),
    ("ETL", "etl", "engineering"),
    ("Data Engineering", "data-engineering", "engineering"),
    ("Machine Learning", "machine-learning", "ai"),
    ("Statistics", "statistics", "analytics"),
    ("Spark", "spark", "engineering"),
    ("LLM", "llm", "ai"),
    ("Onchain Analytics", "onchain-analytics", "analytics"),
    ("PostgreSQL", "postgresql", "engineering"),
    ("Research", "research", "analytics"),
]


OFFICIAL_INGEST_SOURCES = [
    {
        "name": "Nansen",
        "website_url": "https://www.nansen.ai/careers",
        "connector_type": "greenhouse",
        "board_token": "nansen",
        "source_type": OpportunitySourceType.OFFICIAL_COMPANY,
        "trust_level": OpportunitySourceTrustLevel.HIGH,
    },
    {
        "name": "Dune",
        "website_url": "https://dune.com/careers",
        "connector_type": "ashby",
        "board_token": "dune",
        "source_type": OpportunitySourceType.OFFICIAL_COMPANY,
        "trust_level": OpportunitySourceTrustLevel.HIGH,
    },
    {
        "name": "TRM Labs",
        "website_url": "https://www.trmlabs.com/careers",
        "connector_type": "ashby",
        "board_token": "trm-labs",
        "source_type": OpportunitySourceType.OFFICIAL_COMPANY,
        "trust_level": OpportunitySourceTrustLevel.HIGH,
    },
    {
        "name": "Consensys",
        "website_url": "https://consensys.io/open-roles",
        "connector_type": "greenhouse",
        "board_token": "consensys",
        "source_type": OpportunitySourceType.OFFICIAL_COMPANY,
        "trust_level": OpportunitySourceTrustLevel.HIGH,
    },
    {
        "name": "OpenZeppelin",
        "website_url": "https://www.openzeppelin.com/jobs",
        "connector_type": "greenhouse",
        "board_token": "openzeppelin",
        "source_type": OpportunitySourceType.OFFICIAL_COMPANY,
        "trust_level": OpportunitySourceTrustLevel.HIGH,
    },
    {
        "name": "Phantom",
        "website_url": "https://phantom.com/jobs",
        "connector_type": "ashby",
        "board_token": "phantom",
        "source_type": OpportunitySourceType.OFFICIAL_COMPANY,
        "trust_level": OpportunitySourceTrustLevel.HIGH,
    },
    {
        "name": "ETHGlobal",
        "website_url": "https://ethglobal.com/events",
        "connector_type": "ethglobal",
        "config": {"events_url": "https://ethglobal.com/events"},
        "source_type": OpportunitySourceType.HACKATHON_PLATFORM,
        "trust_level": OpportunitySourceTrustLevel.HIGH,
    },
    {
        "name": "Colosseum",
        "website_url": "https://colosseum.com/hackathon",
        "connector_type": "colosseum",
        "config": {"listing_url": "https://colosseum.com/hackathon/__data.json"},
        "source_type": OpportunitySourceType.HACKATHON_PLATFORM,
        "trust_level": OpportunitySourceTrustLevel.HIGH,
    },
    {
        "name": "Devpost Blockchain",
        "website_url": "https://devpost.com/c/blockchain",
        "connector_type": "devpost",
        "config": {"listing_url": "https://devpost.com/c/blockchain"},
        "source_type": OpportunitySourceType.HACKATHON_PLATFORM,
        "trust_level": OpportunitySourceTrustLevel.HIGH,
    },
    {
        "name": "Devfolio",
        "website_url": "https://devfolio.co/explore",
        "connector_type": "devfolio",
        "config": {"listing_url": "https://api.devfolio.co/api/hackathons?filter=application_open&page=1&size=20"},
        "source_type": OpportunitySourceType.HACKATHON_PLATFORM,
        "trust_level": OpportunitySourceTrustLevel.HIGH,
    },
    {
        "name": "DoraHacks",
        "website_url": "https://dorahacks.io/hackathon",
        "connector_type": "dorahacks",
        "config": {"listing_url": "https://dorahacks.io/hackathon?status=upcoming"},
        "source_type": OpportunitySourceType.HACKATHON_PLATFORM,
        "trust_level": OpportunitySourceTrustLevel.HIGH,
    },
    {
        "name": "Encode Club",
        "website_url": "https://www.encodeclub.com/programmes",
        "connector_type": "encode",
        "config": {"listing_url": "https://www.encodeclub.com/programmes"},
        "source_type": OpportunitySourceType.HACKATHON_PLATFORM,
        "trust_level": OpportunitySourceTrustLevel.HIGH,
    },
    {
        "name": "Superteam Earn",
        "website_url": "https://superteam.fun/earn",
        "connector_type": "superteam",
        "config": {"listing_url": "https://superteam.fun/api/listings"},
        "source_type": OpportunitySourceType.COMMUNITY,
        "trust_level": OpportunitySourceTrustLevel.HIGH,
    },
]

# Boards without a verified public API/RSS path — catalogued for ops, not auto-synced.
MANUAL_BOARD_STUBS = [
    {
        "name": "CryptoJobsList",
        "website_url": "https://cryptojobslist.com",
        "note": "No safe public API configured. Use Manual listings or wait for an official feed.",
    },
    {
        "name": "Web3.career",
        "website_url": "https://web3.career",
        "note": "Aggregator. Prefer employer Greenhouse/Ashby/Lever boards. Manual curation only.",
    },
    {
        "name": "Crypto.jobs",
        "website_url": "https://crypto.jobs",
        "note": "No documented public job API. Disabled pending official endpoint.",
    },
    {
        "name": "CryptocurrencyJobs.co",
        "website_url": "https://cryptocurrencyjobs.co",
        "note": "No documented public job API. Manual curation only.",
    },
    {
        "name": "FindWeb3",
        "website_url": "https://www.findweb3.com",
        "note": "No documented public job API. Manual curation only.",
    },
    {
        "name": "Remote3",
        "website_url": "https://www.remote3.co",
        "note": "No documented public job API. Manual curation only. Also useful as a remote Web3 discovery board.",
        "source_role": "discovery",
    },
    {
        "name": "Solana Jobs",
        "website_url": "https://jobs.solana.com",
        "note": "Prefer official employer ATS connectors when available.",
    },
    {
        "name": "Dragonfly Jobs",
        "website_url": "https://www.dragonfly.xyz/careers",
        "note": "Use Greenhouse/Ashby/Lever if the board token is public; otherwise manual.",
    },
    {
        "name": "Rare Talent",
        "website_url": "https://raretalent.io",
        "note": "No documented public job API. Manual curation only.",
    },
    {
        "name": "Hashtag Web3",
        "website_url": "https://hashtagweb3.com",
        "note": "No documented public job API. Manual curation only.",
    },
    {
        "name": "Remote OK",
        "website_url": "https://remoteok.com",
        "note": "Public JSON exists but is rate-limited/ToS-sensitive. Not enabled until reviewed.",
    },
]

# Hackathon / builder-event discovery boards — review-only, no automation claimed.
HACKATHON_DISCOVERY_STUBS = [
    {
        "name": "GitHub web3-hackathons",
        "website_url": "https://github.com/goweb3ig/web3-hackathons",
        "note": "Community-curated markdown list. Discovery / manual import only — no scraper.",
        "source_type": OpportunitySourceType.HACKATHON_PLATFORM,
    },
    {
        "name": "Dev.events",
        "website_url": "https://dev.events",
        "note": "Broad developer events. Filter Web3 manually. No verified public API for automation.",
        "source_type": OpportunitySourceType.HACKATHON_PLATFORM,
    },
    {
        "name": "HackQuest",
        "website_url": "https://www.hackquest.io",
        "note": "Learning + hackathon discovery. Manual curation until an official listing API is reviewed.",
        "source_type": OpportunitySourceType.HACKATHON_PLATFORM,
    },
]

# Bounty / earn discovery boards — review-only, no automation claimed.
BOUNTY_DISCOVERY_STUBS = [
    {
        "name": "Pond",
        "website_url": "https://pond.xyz",
        "note": "Bounty / quest discovery. Manual curation only until an official listing API is approved.",
        "source_type": OpportunitySourceType.COMMUNITY,
    },
    {
        "name": "Immunefi",
        "website_url": "https://immunefi.com",
        "note": "Bug bounty platform. Prefer official program pages; no scraper until ToS/API reviewed.",
        "source_type": OpportunitySourceType.COMMUNITY,
    },
    {
        "name": "Gitcoin",
        "website_url": "https://www.gitcoin.co",
        "note": "Grants and bounties mix. Manual curation; do not auto-ingest without a trusted feed.",
        "source_type": OpportunitySourceType.COMMUNITY,
    },
]


def seed_opportunity_taxonomy(db: Session) -> None:
    for name, slug, description, sort_order in CAREER_PATHS:
        existing = db.scalar(select(CareerPath).where(CareerPath.slug == slug))
        if existing:
            existing.name = name
            existing.description = description
            existing.sort_order = sort_order
            existing.is_active = True
            continue
        db.add(
            CareerPath(
                name=name,
                slug=slug,
                description=description,
                sort_order=sort_order,
                is_active=True,
            )
        )

    for name, slug, category in SKILLS:
        existing = db.scalar(select(Skill).where(Skill.slug == slug))
        if existing:
            existing.name = name
            existing.category = category
            existing.is_active = True
            continue
        db.add(Skill(name=name, slug=slug, category=category, is_active=True))

    manual = db.scalar(select(OpportunitySource).where(OpportunitySource.name == "Manual"))
    if not manual:
        db.add(
            OpportunitySource(
                name="Manual",
                website_url=None,
                source_type=OpportunitySourceType.MANUAL,
                trust_level=OpportunitySourceTrustLevel.MEDIUM,
                automation_enabled=False,
                auto_publish_allowed=False,
                connector_type="manual",
                health_status=OpportunitySourceHealth.UNKNOWN,
                is_active=True,
            )
        )

    for spec in OFFICIAL_INGEST_SOURCES:
        existing = db.scalar(select(OpportunitySource).where(OpportunitySource.name == spec["name"]))
        config = spec.get("config") or {"board_token": spec["board_token"]}
        caps = {
            "supports_automation": True,
            "supports_api": spec["connector_type"] in {"colosseum", "devfolio", "superteam", "encode", "greenhouse", "ashby", "lever"},
            "supports_rss": spec["connector_type"] == "rss",
            "supports_html": spec["connector_type"] in {"ethglobal", "devpost", "dorahacks", "encode"},
            "supports_search": False,
            "requires_review": True,
        }
        if existing:
            existing.website_url = spec["website_url"]
            existing.source_type = spec["source_type"]
            existing.connector_type = spec["connector_type"]
            existing.config = config
            existing.source_role = OpportunitySourceRole.DIRECT
            existing.capabilities = caps
            existing.auto_publish_allowed = False
            continue
        db.add(
            OpportunitySource(
                name=spec["name"],
                website_url=spec["website_url"],
                source_type=spec["source_type"],
                trust_level=spec["trust_level"],
                automation_enabled=True,
                auto_publish_allowed=False,
                connector_type=spec["connector_type"],
                config=config,
                source_role=OpportunitySourceRole.DIRECT,
                capabilities=caps,
                health_status=OpportunitySourceHealth.UNKNOWN,
                is_active=True,
            )
        )

    for stub in [*MANUAL_BOARD_STUBS, *HACKATHON_DISCOVERY_STUBS, *BOUNTY_DISCOVERY_STUBS]:
        existing = db.scalar(select(OpportunitySource).where(OpportunitySource.name == stub["name"]))
        role = stub.get("source_role") or (
            OpportunitySourceRole.DISCOVERY
            if stub in HACKATHON_DISCOVERY_STUBS or stub in BOUNTY_DISCOVERY_STUBS
            else OpportunitySourceRole.MANUAL
        )
        if isinstance(role, str):
            role = OpportunitySourceRole(role)
        source_type = stub.get("source_type") or OpportunitySourceType.JOB_BOARD
        caps = {
            "supports_automation": False,
            "supports_api": False,
            "supports_rss": False,
            "supports_search": False,
            "requires_review": True,
            "supports_bounties": stub in BOUNTY_DISCOVERY_STUBS,
        }
        if existing:
            existing.admin_notes = stub["note"]
            existing.auto_publish_allowed = False
            existing.automation_enabled = False
            existing.connector_type = "manual"
            existing.is_active = False
            existing.source_role = role
            existing.capabilities = caps
            continue
        db.add(
            OpportunitySource(
                name=stub["name"],
                website_url=stub["website_url"],
                base_url=stub["website_url"],
                source_type=source_type,
                trust_level=OpportunitySourceTrustLevel.LOW,
                automation_enabled=False,
                auto_publish_allowed=False,
                connector_type="manual",
                config={},
                attribution_required=True,
                admin_notes=stub["note"],
                source_role=role,
                capabilities=caps,
                health_status=OpportunitySourceHealth.UNKNOWN,
                is_active=False,
            )
        )
    db.flush()
