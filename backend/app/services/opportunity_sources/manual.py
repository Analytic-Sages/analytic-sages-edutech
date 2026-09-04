from __future__ import annotations

from app.models.opportunity import OpportunitySource
from app.services.opportunity_sources.base import ConnectorCapabilities, OpportunityConnector, RawOpportunity


class ManualConnector:
    """Placeholder for boards without a safe public API/RSS ingestion path."""

    connector_type = "manual"
    capabilities = ConnectorCapabilities(
        supports_search=False,
        supports_pagination=False,
        ingestion_method="manual",
    )

    def fetch(self, source: OpportunitySource) -> list[RawOpportunity]:
        return []


__all__ = ["ManualConnector"]
