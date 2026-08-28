"""Seed career paths, skills, and the Manual opportunity source. No fake listings."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.opportunity import (
    CareerPath,
    OpportunitySource,
    OpportunitySourceHealth,
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
        config = {"board_token": spec["board_token"]}
        if existing:
            existing.website_url = spec["website_url"]
            existing.source_type = spec["source_type"]
            existing.connector_type = spec["connector_type"]
            existing.config = config
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
                health_status=OpportunitySourceHealth.UNKNOWN,
                is_active=True,
            )
        )
    db.flush()
