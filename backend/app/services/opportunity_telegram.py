from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.opportunity import Opportunity, OpportunityStatus
from app.services.opportunity_urls import hostname_of, validate_http_url

logger = logging.getLogger(__name__)
TELEGRAM_HOST = "api.telegram.org"
TYPE_EMOJI = {
    "job": "💼",
    "internship": "🌱",
    "fellowship": "🎓",
    "hackathon": "🏆",
    "grant": "💰",
    "bounty": "🎯",
    "research": "🔬",
    "other": "🔍",
}


class OpportunityTelegramService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()

    @property
    def configured(self) -> bool:
        return bool((self.settings.telegram_bot_token or "").strip() and (self.settings.telegram_channel_id or "").strip())

    def announce(self, opportunity_id, *, force: bool = False) -> dict:
        opportunity = self.db.get(Opportunity, opportunity_id)
        if not opportunity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
        if opportunity.status != OpportunityStatus.PUBLISHED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only published opportunities can be announced")
        if opportunity.telegram_announced_at is not None and not force:
            return {"status": "already_announced", "announced_at": opportunity.telegram_announced_at.isoformat()}
        if not self.settings.opportunities_public:
            return {"status": "skipped", "detail": "Opportunities hub is private until go-live"}
        if not self.configured:
            return {"status": "skipped", "detail": "Telegram is not configured"}
        posted = self._post(opportunity)
        if posted:
            from datetime import UTC, datetime

            opportunity.telegram_announced_at = datetime.now(UTC)
            self.db.commit()
            return {"status": "announced", "announced_at": opportunity.telegram_announced_at.isoformat()}
        return {"status": "failed", "detail": "Telegram did not accept the announcement"}

    def announce_on_publish(self, opportunity_id) -> None:
        try:
            result = self.announce(opportunity_id)
            logger.info("telegram_announce opportunity=%s result=%s", opportunity_id, result.get("status"))
        except Exception:
            logger.exception("telegram_announce failed opportunity=%s", opportunity_id)

    def _post(self, opportunity: Opportunity) -> bool:
        token = (self.settings.telegram_bot_token or "").strip()
        chat_id = (self.settings.telegram_channel_id or "").strip()
        url = f"https://{TELEGRAM_HOST}/bot{token}/sendMessage"
        try:
            validate_http_url(url, "telegram_url")
        except HTTPException:
            logger.warning("Telegram bot URL failed validation")
            return False
        frontend = self.settings.frontend_url.rstrip("/")
        listing_url = f"{frontend}/opportunities/{opportunity.slug}"
        kind = getattr(opportunity.opportunity_type, "value", str(opportunity.opportunity_type))
        emoji = TYPE_EMOJI.get(kind, "🔍")
        location = opportunity.location or "Remote"
        path = ""
        primary = next((link.career_path for link in opportunity.career_path_links if link.is_primary), None)
        if primary is None and opportunity.career_path_links:
            primary = opportunity.career_path_links[0].career_path
        if primary:
            path = f"\n🧠 {primary.name}"
        text = (
            f"{emoji} <b>New Opportunity</b>\n\n"
            f"<b>{_escape(opportunity.title)} — {_escape(opportunity.organization_name)}</b>\n\n"
            f"📍 {_escape(location)}\n"
            f"💼 {_escape(kind.replace('_', ' ').title())}"
            f"{path}\n\n"
            f"View details and apply 👇\n"
            f"{listing_url}"
        )
        try:
            with httpx.Client(timeout=15.0, follow_redirects=False) as client:
                response = client.post(
                    url,
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": False,
                    },
                )
                if hostname_of(str(response.url)) != TELEGRAM_HOST:
                    logger.warning("Telegram request left api.telegram.org")
                    return False
                if response.status_code >= 400:
                    logger.warning("Telegram send failed status=%s body=%s", response.status_code, response.text[:300])
                    return False
                return True
        except httpx.HTTPError:
            logger.exception("Telegram send failed")
            return False


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
