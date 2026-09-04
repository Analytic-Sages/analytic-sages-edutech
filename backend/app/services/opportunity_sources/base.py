from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol

from app.models.opportunity import (
    BountyCategory,
    HackathonEventFormat,
    OpportunitySource,
    OpportunityType,
    WorkplaceType,
)

MAX_ITEMS_PER_SYNC = 50
MAX_BODY_BYTES = 2_000_000
FETCH_TIMEOUT_SECONDS = 15.0
USER_AGENT = "AnalyticSagesOpportunitiesBot/1.0 (+https://analyticsages.com)"


@dataclass(frozen=True)
class ConnectorCapabilities:
    supports_search: bool = False
    supports_pagination: bool = False
    supports_date_filter: bool = False
    supports_remote_filter: bool = False
    ingestion_method: str = "api"  # api | rss | html | manual


@dataclass
class RawOpportunity:
    external_id: str
    title: str
    organization_name: str
    description: str = ""
    requirements: str = ""
    location: str = ""
    application_url: str = ""
    source_url: str | None = None
    posted_at: datetime | None = None
    deadline: datetime | None = None
    opportunity_type: OpportunityType | None = None
    workplace_type: WorkplaceType | None = None
    # Optional hackathon / challenge enrichment (ignored for jobs)
    registration_open_at: datetime | None = None
    registration_deadline: datetime | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    submission_deadline: datetime | None = None
    event_format: HackathonEventFormat | None = None
    prize_pool_amount: Decimal | None = None
    prize_currency: str | None = None
    prize_pool_raw: str | None = None
    team_size_min: int | None = None
    team_size_max: int | None = None
    tags: list[str] = field(default_factory=list)
    tracks: list[str] = field(default_factory=list)
    # Optional bounty / earn enrichment
    reward_amount: Decimal | None = None
    reward_token: str | None = None
    reward_currency: str | None = None
    reward_raw: str | None = None
    bounty_category: BountyCategory | None = None
    bounty_deadline: datetime | None = None
    opens_at: datetime | None = None
    winners_announced: bool | None = None
    bounty_skills: list[str] = field(default_factory=list)
    chain_focus: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


class OpportunityConnector(Protocol):
    connector_type: str
    capabilities: ConnectorCapabilities

    def fetch(self, source: OpportunitySource) -> list[RawOpportunity]: ...
