"""Publish-domain hooks for opportunities (Telegram / digest consumers)."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.opportunity import Opportunity, OpportunityStatus, OpportunityType

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OpportunityPublished:
    opportunity_id: UUID
    title: str
    organization: str
    career_tracks: list[str]
    location: str
    application_url: str
    slug: str
    opportunity_type: str = "job"
    event_format: str | None = None
    prize_pool_raw: str | None = None
    registration_deadline: str | None = None
    derived_phase: str | None = None
    reward_raw: str | None = None
    bounty_category: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def build_published_event(opportunity: Opportunity) -> OpportunityPublished:
    tracks = list(opportunity.matched_career_tracks or [])
    if not tracks:
        tracks = [
            link.career_path.slug
            for link in (opportunity.career_path_links or [])
            if link.career_path is not None
        ]
    hackathon = getattr(opportunity, "hackathon_details", None)
    bounty = getattr(opportunity, "bounty_details", None)
    return OpportunityPublished(
        opportunity_id=opportunity.id,
        title=opportunity.title,
        organization=opportunity.organization_name,
        career_tracks=tracks,
        location=opportunity.location or "",
        application_url=opportunity.application_url,
        slug=opportunity.slug,
        opportunity_type=getattr(opportunity.opportunity_type, "value", str(opportunity.opportunity_type)),
        event_format=getattr(hackathon.event_format, "value", None) if hackathon else None,
        prize_pool_raw=hackathon.prize_pool_raw if hackathon else None,
        registration_deadline=(
            hackathon.registration_deadline.isoformat()
            if hackathon and hackathon.registration_deadline
            else (
                bounty.deadline.isoformat()
                if bounty and bounty.deadline
                else (opportunity.deadline.isoformat() if opportunity.deadline else None)
            )
        ),
        derived_phase=(
            hackathon.derived_phase
            if hackathon
            else (bounty.derived_phase if bounty else None)
        ),
        reward_raw=bounty.reward_raw if bounty else None,
        bounty_category=getattr(bounty.category, "value", None) if bounty else None,
    )


def emit_opportunity_published(opportunity: Opportunity) -> OpportunityPublished:
    """Structured hook for future Telegram / newsletter subscribers."""
    event = build_published_event(opportunity)
    logger.info(
        "opportunity.published id=%s slug=%s type=%s org=%s tracks=%s phase=%s reward=%s",
        event.opportunity_id,
        event.slug,
        event.opportunity_type,
        event.organization,
        ",".join(event.career_tracks) or "-",
        event.derived_phase or "-",
        event.reward_raw or event.prize_pool_raw or "-",
    )
    return event


def recently_published_hackathons(
    db: Session,
    *,
    within_days: int = 7,
    limit: int = 50,
) -> list[Opportunity]:
    """Digest helper: published hackathons/challenges from the last N days."""
    since = datetime.now(UTC) - timedelta(days=within_days)
    return list(
        db.scalars(
            select(Opportunity)
            .options(selectinload(Opportunity.hackathon_details))
            .where(
                Opportunity.status == OpportunityStatus.PUBLISHED,
                Opportunity.opportunity_type.in_(
                    (OpportunityType.HACKATHON, OpportunityType.CHALLENGE)
                ),
                Opportunity.published_at.is_not(None),
                Opportunity.published_at >= since,
            )
            .order_by(Opportunity.published_at.desc())
            .limit(limit)
        ).all()
    )


def recently_published_bounties(
    db: Session,
    *,
    within_days: int = 7,
    limit: int = 50,
) -> list[Opportunity]:
    """Digest helper: published bounties from the last N days."""
    since = datetime.now(UTC) - timedelta(days=within_days)
    return list(
        db.scalars(
            select(Opportunity)
            .options(selectinload(Opportunity.bounty_details))
            .where(
                Opportunity.status == OpportunityStatus.PUBLISHED,
                Opportunity.opportunity_type == OpportunityType.BOUNTY,
                Opportunity.published_at.is_not(None),
                Opportunity.published_at >= since,
            )
            .order_by(Opportunity.published_at.desc())
            .limit(limit)
        ).all()
    )
