"""Derived lifecycle phases for bounties / quests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import Enum

CLOSING_SOON_DAYS = 7


class BountyPhase(str, Enum):
    OPEN = "open"
    CLOSING_SOON = "closing_soon"
    ENDED = "ended"
    UNKNOWN = "unknown"


PHASE_RANK = {
    BountyPhase.CLOSING_SOON: 0,
    BountyPhase.OPEN: 1,
    BountyPhase.UNKNOWN: 2,
    BountyPhase.ENDED: 3,
}


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def derive_bounty_phase(
    *,
    opens_at: datetime | None = None,
    deadline: datetime | None = None,
    winners_announced: bool = False,
    fallback_deadline: datetime | None = None,
    now: datetime | None = None,
) -> BountyPhase:
    current = _aware(now) or datetime.now(UTC)
    due = _aware(deadline) or _aware(fallback_deadline)
    open_at = _aware(opens_at)

    if winners_announced:
        return BountyPhase.ENDED
    if due is not None and current > due:
        return BountyPhase.ENDED
    if open_at is not None and current < open_at:
        return BountyPhase.UNKNOWN
    if due is not None and current <= due <= current + timedelta(days=CLOSING_SOON_DAYS):
        return BountyPhase.CLOSING_SOON
    if due is not None or open_at is not None:
        return BountyPhase.OPEN
    return BountyPhase.UNKNOWN


def closes_in_days(
    deadline: datetime | None,
    *,
    fallback_deadline: datetime | None = None,
    now: datetime | None = None,
) -> int | None:
    due = _aware(deadline) or _aware(fallback_deadline)
    if due is None:
        return None
    current = _aware(now) or datetime.now(UTC)
    delta = due - current
    if delta.total_seconds() < 0:
        return None
    return max(0, int(delta.total_seconds() // 86400))
