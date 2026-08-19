"""Idempotent seed for a featured public workshop (Coming soon until a date is set)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event, EventType
from app.services.seed_self_paced import DUNE_SLUG

FEATURED_EVENT_SLUG = "dune-analytics-building-your-first-defi-dashboard"
TEST_EVENT_SLUG = "test-dune-workshop"


def seed_featured_event(db: Session) -> Event | None:
    leftover = db.scalar(select(Event).where(Event.slug == TEST_EVENT_SLUG))
    if leftover:
        db.delete(leftover)
        db.flush()

    existing = db.scalar(select(Event).where(Event.slug == FEATURED_EVENT_SLUG))
    if existing:
        start = existing.starts_at
        if start is not None:
            local = start.astimezone(start.tzinfo) if start.tzinfo else start
            if local.year == 2026 and local.month == 9 and local.day == 5:
                existing.starts_at = None
                existing.ends_at = None
        existing.published = True
        existing.cancelled = False
        return existing

    event = Event(
        slug=FEATURED_EVENT_SLUG,
        title="Dune Analytics: Building Your First DeFi Dashboard",
        event_type=EventType.WORKSHOP,
        short_description=(
            "A free live workshop on querying on-chain data and assembling a first DeFi dashboard in Dune."
        ),
        description=(
            "Join Analytic Sages for a free live workshop on Dune Analytics. We will walk through "
            "practical SQL for blockchain data, dashboard parameters, and how to ship a first DeFi "
            "dashboard you can keep iterating on after the session.\n\n"
            "Date and join link will be announced here. Register with your Analytic Sages account "
            "when registration opens. The free self-paced Dune course is available if you want to "
            "keep practicing after the workshop."
        ),
        cover_image="/4.png",
        starts_at=None,
        ends_at=None,
        timezone="Africa/Lagos",
        price=0,
        currency="USD",
        host_name="Analytic Sages",
        learn_topics=[
            "Query on-chain data in Dune SQL",
            "Use dashboard parameters and date filters",
            "Assemble a first DeFi dashboard you can share",
        ],
        audience=[
            "Analysts new to Dune",
            "Builders who want a practical DeFi dashboard workflow",
            "Students in the free Dune self-paced course",
        ],
        prerequisites="A free Dune account. No paid Dune plan required.",
        related_course_slug=DUNE_SLUG,
        seo_title="Dune Analytics workshop: build your first DeFi dashboard",
        seo_description=(
            "Free Analytic Sages Dune workshop. Date coming soon. Register with your account when "
            "the session is announced."
        ),
        published=True,
        cancelled=False,
    )
    db.add(event)
    db.flush()
    return event
