from __future__ import annotations

import json
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.opportunity import CareerPath, Opportunity
from app.schemas.opportunities import OpportunityReviewAssistPublic
from app.services.llm_complete import complete_json, llm_configured


class OpportunityReviewAssistService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()

    @property
    def configured(self) -> bool:
        return llm_configured(self.settings)

    def review(self, opportunity_id) -> OpportunityReviewAssistPublic:
        opportunity = self.db.get(Opportunity, opportunity_id)
        if not opportunity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
        if not self.configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Review assist is not configured. Set OPENAI_API_KEY or GEMINI_API_KEY.",
            )
        paths = _active_paths(self.db)
        payload, provider = self._complete(opportunity, [path.slug for path in paths])
        payload["generated_at"] = datetime.now(UTC).isoformat()
        payload["provider"] = provider
        opportunity.review_assist = payload
        self.db.commit()
        return OpportunityReviewAssistPublic(
            configured=True,
            notes=payload.get("notes"),
            suggested_type=payload.get("suggested_type"),
            suggested_career_paths=list(payload.get("suggested_career_paths") or []),
            risk_notes=list(payload.get("risk_notes") or []),
            generated_at=datetime.now(UTC),
            provider=provider,
        )

    def _complete(self, opportunity: Opportunity, path_slugs: list[str]) -> tuple[dict, str]:
        parsed, _grounded, provider = complete_json(
            self.settings,
            instructions=(
                "You assist Analytic Sages admins reviewing career opportunities. "
                "Never decide to publish. Return JSON with notes, suggested_type "
                "(job|internship|fellowship|hackathon|grant|bounty|research|other), "
                "suggested_career_paths (from the allowed list only), and risk_notes."
            ),
            user_content=json.dumps(
                {
                    "title": opportunity.title,
                    "organization_name": opportunity.organization_name,
                    "description": (opportunity.description or "")[:4000],
                    "allowed_career_paths": path_slugs,
                }
            ),
            with_search=False,
        )
        allowed = set(path_slugs)
        suggested = [slug for slug in parsed.get("suggested_career_paths") or [] if slug in allowed]
        return (
            {
                "notes": str(parsed.get("notes") or "")[:2000] or None,
                "suggested_type": parsed.get("suggested_type")
                if parsed.get("suggested_type")
                in {
                    "job",
                    "internship",
                    "fellowship",
                    "hackathon",
                    "grant",
                    "bounty",
                    "research",
                    "other",
                }
                else None,
                "suggested_career_paths": suggested,
                "risk_notes": [str(item)[:300] for item in (parsed.get("risk_notes") or [])[:8]],
            },
            provider,
        )


def _active_paths(db: Session):
    from sqlalchemy import select

    return db.scalars(select(CareerPath).where(CareerPath.is_active.is_(True)).order_by(CareerPath.sort_order)).all()
