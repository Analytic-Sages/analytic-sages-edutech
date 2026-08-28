from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from app.models.opportunity import OpportunitySource, OpportunityType, WorkplaceType

MAX_ITEMS_PER_SYNC = 50
MAX_BODY_BYTES = 2_000_000
FETCH_TIMEOUT_SECONDS = 15.0
USER_AGENT = "AnalyticSagesOpportunitiesBot/1.0 (+https://analyticsages.com)"


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
    raw_data: dict[str, Any] = field(default_factory=dict)


class OpportunityConnector(Protocol):
    connector_type: str

    def fetch(self, source: OpportunitySource) -> list[RawOpportunity]: ...
