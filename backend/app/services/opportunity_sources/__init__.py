from __future__ import annotations

from fastapi import HTTPException, status

from app.models.opportunity import OpportunitySource
from app.services.opportunity_sources.ashby import AshbyConnector
from app.services.opportunity_sources.base import OpportunityConnector, RawOpportunity
from app.services.opportunity_sources.colosseum import ColosseumConnector
from app.services.opportunity_sources.devfolio import DevfolioConnector
from app.services.opportunity_sources.devpost import DevpostConnector
from app.services.opportunity_sources.dorahacks import DorahacksConnector
from app.services.opportunity_sources.encode import EncodeConnector
from app.services.opportunity_sources.ethglobal import EthglobalConnector
from app.services.opportunity_sources.greenhouse import GreenhouseConnector
from app.services.opportunity_sources.lever import LeverConnector
from app.services.opportunity_sources.manual import ManualConnector
from app.services.opportunity_sources.rss import RssConnector
from app.services.opportunity_sources.superteam import SuperteamConnector

CONNECTORS: dict[str, OpportunityConnector] = {
    "rss": RssConnector(),
    "greenhouse": GreenhouseConnector(),
    "ashby": AshbyConnector(),
    "lever": LeverConnector(),
    "ethglobal": EthglobalConnector(),
    "colosseum": ColosseumConnector(),
    "devpost": DevpostConnector(),
    "devfolio": DevfolioConnector(),
    "dorahacks": DorahacksConnector(),
    "encode": EncodeConnector(),
    "superteam": SuperteamConnector(),
    "manual": ManualConnector(),
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
