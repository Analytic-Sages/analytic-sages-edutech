from __future__ import annotations

import logging
from collections import Counter
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.opportunity import Opportunity, OpportunityDigestRun
from app.models.user import User
from app.services.email import EmailService
from app.services.opportunities import OpportunityService

logger = logging.getLogger(__name__)
TYPE_LABELS = {
    "job": "Jobs",
    "internship": "Internships",
    "fellowship": "Fellowships",
    "hackathon": "Hackathons",
    "grant": "Grants",
    "bounty": "Bounties",
    "research": "Research",
    "other": "Other",
}


class OpportunityDigestService:
    def __init__(self, db: Session, settings: Settings | None = None, email: EmailService | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.email = email or EmailService(self.settings)
        self.opportunities = OpportunityService(db)

    def send_weekly(self, *, actor: User | None = None, force: bool = False) -> dict:
        if not self.settings.opportunities_public:
            return {
                "status": "skipped",
                "detail": "Opportunities hub is private until go-live",
                "listing_count": 0,
            }
        now = datetime.now(UTC)
        if not force:
            latest = self.db.scalar(select(OpportunityDigestRun).order_by(OpportunityDigestRun.sent_at.desc()).limit(1))
            if latest and latest.sent_at and latest.sent_at > now - timedelta(days=6):
                return {
                    "status": "skipped",
                    "detail": "A digest was already sent in the last 6 days",
                    "listing_count": latest.listing_count,
                }
        since = now - timedelta(days=7)
        rows = self.db.scalars(
            select(Opportunity)
            .options(*self.opportunities._detail_load())
            .where(
                self.opportunities._visible_now(now),
                Opportunity.published_at.is_not(None),
                Opportunity.published_at >= since,
            )
            .order_by(Opportunity.published_at.desc())
        ).all()
        active = list(rows)
        counts = Counter(getattr(row.opportunity_type, "value", str(row.opportunity_type)) for row in active)
        listings = [
            {
                "title": row.title,
                "organization_name": row.organization_name,
                "opportunity_type": getattr(row.opportunity_type, "value", str(row.opportunity_type)),
                "url": f"{self.settings.frontend_url.rstrip('/')}/opportunities/{row.slug}",
            }
            for row in active[:20]
        ]
        sent = self.email.send_opportunity_digest(counts=dict(counts), listings=listings, total=len(active))
        run = OpportunityDigestRun(
            listing_count=len(active),
            item_ids=[str(row.id) for row in active],
            status="sent" if sent else "logged",
            triggered_by=actor.id if actor else None,
        )
        if not sent and self.email.newsletter_ready:
            run.status = "failed"
            run.error_message = "Resend rejected the digest broadcast"
        self.db.add(run)
        self.db.commit()
        if run.status == "failed":
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not send the weekly digest")
        return {"status": run.status, "listing_count": run.listing_count, "counts": dict(counts)}
