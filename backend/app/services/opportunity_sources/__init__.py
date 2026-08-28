from __future__ import annotations

from fastapi import HTTPException, status

from app.models.opportunity import OpportunitySource
from app.services.opportunity_sources.base import OpportunityConnector, RawOpportunity
from app.services.opportunity_sources.ashby import AshbyConnector
from app.services.opportunity_sources.greenhouse import GreenhouseConnector
from app.services.opportunity_sources.lever import LeverConnector
from app.services.opportunity_sources.rss import RssConnector

CONNECTORS: dict[str, OpportunityConnector] = {
    "rss": RssConnector(),
    "greenhouse": GreenhouseConnector(),
    "ashby": AshbyConnector(),
    "lever": LeverConnector(),
}


def get_connector(source: OpportunitySource) -> OpportunityConnector:
    connector = CONNECTORS.get(source.connector_type)
    if connector is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported connector type: {source.connector_type}",
        )
    return connector


__all__ = ["CONNECTORS", "RawOpportunity", "get_connector"]
