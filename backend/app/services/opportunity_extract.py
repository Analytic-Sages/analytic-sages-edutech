"""AI extraction for opportunity pages — structured output, no invented fields."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from app.core.config import Settings, get_settings
from app.models.opportunity import OpportunityType
from app.services.llm_complete import complete_json, llm_configured
from app.services.opportunity_sources.base import RawOpportunity

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {item.value for item in OpportunityType}
MIN_CONFIDENCE_USE = 0.55
THIN_DESCRIPTION_CHARS = 280


@dataclass
class ExtractedOpportunity:
    title: str | None = None
    organization_name: str | None = None
    opportunity_type: OpportunityType | None = None
    description: str | None = None
    location: str | None = None
    deadline: datetime | None = None
    skills: list[str] = field(default_factory=list)
    compensation_text: str | None = None
    confidence: float = 0.0
    provider: str | None = None
    fields_filled: list[str] = field(default_factory=list)

    def to_metadata(self) -> dict:
        return {
            "confidence": round(self.confidence, 3),
            "provider": self.provider,
            "fields_filled": list(self.fields_filled),
            "opportunity_type": self.opportunity_type.value if self.opportunity_type else None,
        }


def extraction_enabled(settings: Settings | None = None) -> bool:
    cfg = settings or get_settings()
    if not getattr(cfg, "opportunity_ai_extraction_enabled", True):
        return False
    return llm_configured(cfg)


def is_incomplete_raw(raw: RawOpportunity) -> bool:
    """True when connector output is too thin for reliable review without extraction."""
    description = (raw.description or "").strip()
    if len(description) < THIN_DESCRIPTION_CHARS:
        return True
    if not (raw.organization_name or "").strip():
        return True
    if not (raw.title or "").strip():
        return True
    return False


def validate_extraction_payload(payload: dict, *, provider: str | None = None) -> ExtractedOpportunity:
    """Strictly validate LLM JSON. Unknown / invented values stay null."""
    if not isinstance(payload, dict):
        return ExtractedOpportunity(provider=provider)

    confidence = _confidence(payload.get("confidence"))
    filled: list[str] = []

    title = _optional_str(payload.get("title"), max_len=255)
    organization = _optional_str(payload.get("organization_name"), max_len=255)
    description = _optional_str(payload.get("description"), max_len=8000)
    location = _optional_str(payload.get("location"), max_len=255)
    compensation = _optional_str(payload.get("compensation_text"), max_len=255)
    opp_type = _optional_type(payload.get("opportunity_type"))
    deadline = _optional_deadline(payload.get("deadline"))
    skills = _optional_skills(payload.get("skills"))

    if title:
        filled.append("title")
    if organization:
        filled.append("organization_name")
    if description:
        filled.append("description")
    if location:
        filled.append("location")
    if deadline:
        filled.append("deadline")
    if opp_type:
        filled.append("opportunity_type")
    if skills:
        filled.append("skills")
    if compensation:
        filled.append("compensation_text")

    return ExtractedOpportunity(
        title=title,
        organization_name=organization,
        opportunity_type=opp_type,
        description=description,
        location=location,
        deadline=deadline,
        skills=skills,
        compensation_text=compensation,
        confidence=confidence,
        provider=provider,
        fields_filled=filled,
    )


def extract_from_page_text(
    page_text: str,
    *,
    page_url: str,
    settings: Settings | None = None,
    hint_title: str | None = None,
    hint_organization: str | None = None,
    hint_type: str | None = None,
) -> ExtractedOpportunity | None:
    """Extract structured fields from fetched page text. Returns None if LLM unavailable or invalid."""
    cfg = settings or get_settings()
    if not extraction_enabled(cfg):
        return None
    text = (page_text or "").strip()
    if len(text) < 40:
        return None

    instructions = (
        "Extract structured opportunity fields from the official page text. "
        "Return JSON only with keys: title, organization_name, opportunity_type, "
        "description, location, deadline, skills, compensation_text, confidence. "
        "opportunity_type must be one of: job, internship, fellowship, hackathon, "
        "grant, bounty, challenge, research, other — or null if unclear. "
        "deadline must be ISO-8601 date or null. skills is a string array or []. "
        "confidence is 0-1 for how complete and faithful the extraction is. "
        "CRITICAL: Do not invent missing information. Use null for unknown fields. "
        "Do not copy unrelated site chrome. Prefer the primary listing content."
    )
    user_payload = {
        "page_url": page_url,
        "hint_title": hint_title,
        "hint_organization": hint_organization,
        "hint_type": hint_type,
        "page_text": text[:12_000],
    }
    try:
        parsed, _grounded, provider = complete_json(
            cfg,
            instructions=instructions,
            user_content=json.dumps(user_payload),
            with_search=False,
        )
    except Exception:
        logger.exception("Opportunity extraction LLM call failed")
        return None
    return validate_extraction_payload(parsed, provider=provider)


def merge_raw_with_extraction(
    raw: RawOpportunity,
    extracted: ExtractedOpportunity,
    *,
    min_confidence: float = MIN_CONFIDENCE_USE,
) -> RawOpportunity:
    """Fill only missing/thin fields from extraction when confidence is high enough."""
    if extracted.confidence < min_confidence:
        return raw

    title = (raw.title or "").strip() or (extracted.title or "")
    organization = (raw.organization_name or "").strip() or (extracted.organization_name or "")
    description = (raw.description or "").strip()
    if len(description) < THIN_DESCRIPTION_CHARS and extracted.description:
        description = extracted.description
    location = (raw.location or "").strip() or (extracted.location or "")
    deadline = raw.deadline or extracted.deadline
    opportunity_type = raw.opportunity_type or extracted.opportunity_type

    tags = list(raw.tags)
    for skill in extracted.skills:
        if skill not in tags:
            tags.append(skill)

    raw_data = dict(raw.raw_data or {})
    raw_data["ai_extraction"] = extracted.to_metadata()

    return RawOpportunity(
        external_id=raw.external_id,
        title=title[:255],
        organization_name=organization[:255],
        description=description[:20000],
        requirements=raw.requirements,
        location=location[:255],
        application_url=raw.application_url,
        source_url=raw.source_url,
        organization_logo_url=raw.organization_logo_url,
        posted_at=raw.posted_at,
        deadline=deadline,
        opportunity_type=opportunity_type,
        workplace_type=raw.workplace_type,
        registration_open_at=raw.registration_open_at,
        registration_deadline=raw.registration_deadline,
        start_at=raw.start_at,
        end_at=raw.end_at,
        submission_deadline=raw.submission_deadline,
        event_format=raw.event_format,
        prize_pool_amount=raw.prize_pool_amount,
        prize_currency=raw.prize_currency,
        prize_pool_raw=raw.prize_pool_raw,
        team_size_min=raw.team_size_min,
        team_size_max=raw.team_size_max,
        tags=tags[:24],
        tracks=list(raw.tracks),
        reward_amount=raw.reward_amount,
        reward_token=raw.reward_token,
        reward_currency=raw.reward_currency,
        reward_raw=raw.reward_raw,
        bounty_category=raw.bounty_category,
        bounty_deadline=raw.bounty_deadline,
        opens_at=raw.opens_at,
        winners_announced=raw.winners_announced,
        bounty_skills=list(raw.bounty_skills),
        chain_focus=raw.chain_focus,
        raw_data=raw_data,
    )


def _optional_str(value: object, *, max_len: int) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "n/a", "unknown"}:
        return None
    return text[:max_len]


def _optional_type(value: object) -> OpportunityType | None:
    if value is None:
        return None
    raw = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if raw not in ALLOWED_TYPES:
        return None
    return OpportunityType(raw)


def _optional_deadline(value: object) -> datetime | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw or raw.lower() in {"null", "none", "n/a"}:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        # Allow date-only
        try:
            parsed = datetime.strptime(raw[:10], "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _optional_skills(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    skills: list[str] = []
    for item in value[:16]:
        text = _optional_str(item, max_len=80)
        if text and text not in skills:
            skills.append(text)
    return skills


def _confidence(value: object) -> float:
    if value is None:
        return 0.0
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    if score < 0:
        return 0.0
    if score > 1:
        # Allow 0-100 style
        if score <= 100:
            score = score / 100.0
        else:
            return 0.0
    return round(score, 3)


def confidence_as_decimal(extracted: ExtractedOpportunity) -> Decimal | None:
    if extracted.confidence <= 0:
        return None
    return Decimal(str(round(extracted.confidence * 100, 2)))
