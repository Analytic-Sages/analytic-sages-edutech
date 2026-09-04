"""Persist / refresh opportunity_bounty_details rows."""

from __future__ import annotations

from datetime import UTC, datetime

from app.models.opportunity import Opportunity, OpportunityBountyDetails, OpportunityType
from app.services.bounty_dates import derive_bounty_phase
from app.services.bounty_normalize import BountyDetailsPayload, normalize_bounty_details
from app.services.opportunity_sources.base import RawOpportunity


def upsert_bounty_details(
    opportunity: Opportunity,
    raw: RawOpportunity | None = None,
    *,
    payload: BountyDetailsPayload | None = None,
    now: datetime | None = None,
) -> OpportunityBountyDetails | None:
    if opportunity.opportunity_type != OpportunityType.BOUNTY:
        return None
    details = payload
    if details is None:
        if raw is None:
            return opportunity.bounty_details
        details = normalize_bounty_details(raw, now=now)

    row = opportunity.bounty_details
    if row is None:
        row = OpportunityBountyDetails(opportunity_id=opportunity.id)
        opportunity.bounty_details = row

    row.short_description = details.short_description
    row.listing_url = details.listing_url
    row.reward_amount = details.reward_amount
    row.reward_token = details.reward_token
    row.reward_currency = details.reward_currency
    row.reward_raw = details.reward_raw
    row.reward_min = details.reward_min
    row.reward_max = details.reward_max
    row.category = details.category
    row.opens_at = details.opens_at
    row.deadline = details.deadline
    row.winners_announced = details.winners_announced
    row.skills = list(details.skills)
    row.tags = list(details.tags)
    row.chain_focus = details.chain_focus
    row.derived_phase = details.derived_phase
    row.last_verified_at = now or datetime.now(UTC)

    if details.deadline and opportunity.deadline is None:
        opportunity.deadline = details.deadline

    return row


def refresh_derived_phase(details: OpportunityBountyDetails, *, now: datetime | None = None) -> str:
    phase = derive_bounty_phase(
        opens_at=details.opens_at,
        deadline=details.deadline,
        winners_announced=details.winners_announced,
        now=now,
    )
    details.derived_phase = phase.value
    return phase.value
