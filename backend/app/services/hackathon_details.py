"""Persist / refresh opportunity_hackathon_details rows."""

from __future__ import annotations

from datetime import UTC, datetime

from app.models.opportunity import Opportunity, OpportunityHackathonDetails, OpportunityType
from app.services.hackathon_dates import derive_hackathon_phase
from app.services.hackathon_normalize import HackathonDetailsPayload, normalize_hackathon_details
from app.services.opportunity_sources.base import RawOpportunity

HACKATHON_TYPES = {OpportunityType.HACKATHON, OpportunityType.CHALLENGE}


def upsert_hackathon_details(
    opportunity: Opportunity,
    raw: RawOpportunity | None = None,
    *,
    payload: HackathonDetailsPayload | None = None,
    now: datetime | None = None,
) -> OpportunityHackathonDetails | None:
    if opportunity.opportunity_type not in HACKATHON_TYPES:
        return None
    details = payload
    if details is None:
        if raw is None:
            return opportunity.hackathon_details
        details = normalize_hackathon_details(raw, now=now)

    # Prefer challenge when normalizer upgraded the type
    if details.opportunity_type == OpportunityType.CHALLENGE:
        opportunity.opportunity_type = OpportunityType.CHALLENGE

    row = opportunity.hackathon_details
    if row is None:
        row = OpportunityHackathonDetails(opportunity_id=opportunity.id)
        opportunity.hackathon_details = row

    row.short_description = details.short_description
    row.registration_url = details.registration_url
    row.website_url = details.website_url
    row.registration_open_at = details.registration_open_at
    row.registration_deadline = details.registration_deadline
    row.start_at = details.start_at
    row.end_at = details.end_at
    row.submission_deadline = details.submission_deadline
    row.announcement_at = details.announcement_at
    row.event_format = details.event_format
    row.prize_pool_amount = details.prize_pool_amount
    row.prize_currency = details.prize_currency
    row.prize_pool_raw = details.prize_pool_raw
    row.team_size_min = details.team_size_min
    row.team_size_max = details.team_size_max
    row.team_required = details.team_required
    row.individual_allowed = details.individual_allowed
    row.tags = list(details.tags)
    row.tracks = list(details.tracks)
    row.technology_focus = details.technology_focus
    row.derived_phase = details.derived_phase
    row.last_verified_at = now or datetime.now(UTC)

    # Keep opportunity.deadline aligned with registration close when present
    if details.registration_deadline and (
        opportunity.deadline is None or opportunity.deadline != details.registration_deadline
    ):
        if opportunity.deadline is None:
            opportunity.deadline = details.registration_deadline

    return row


def refresh_derived_phase(details: OpportunityHackathonDetails, *, now: datetime | None = None) -> str:
    phase = derive_hackathon_phase(
        registration_open_at=details.registration_open_at,
        registration_deadline=details.registration_deadline,
        start_at=details.start_at,
        end_at=details.end_at,
        submission_deadline=details.submission_deadline,
        now=now,
    )
    details.derived_phase = phase.value
    return phase.value
