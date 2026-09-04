"""Derived lifecycle phases for hackathons / challenges."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum


class HackathonPhase(str, Enum):
    OPEN = "open"  # registration open / accepting applications
    UPCOMING = "upcoming"  # announced; registration not open yet
    ONGOING = "ongoing"  # event running
    ENDED = "ended"
    UNKNOWN = "unknown"


PHASE_RANK = {
    HackathonPhase.OPEN: 0,
    HackathonPhase.ONGOING: 1,
    HackathonPhase.UPCOMING: 2,
    HackathonPhase.UNKNOWN: 3,
    HackathonPhase.ENDED: 4,
}


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def derive_hackathon_phase(
    *,
    registration_open_at: datetime | None = None,
    registration_deadline: datetime | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    submission_deadline: datetime | None = None,
    fallback_deadline: datetime | None = None,
    now: datetime | None = None,
) -> HackathonPhase:
    """Compute OPEN / UPCOMING / ONGOING / ENDED from available dates.

    Does not change draft/published status — phase is display/sort metadata only.
    """
    current = _aware(now) or datetime.now(UTC)
    reg_open = _aware(registration_open_at)
    reg_close = _aware(registration_deadline) or _aware(fallback_deadline)
    start = _aware(start_at)
    end = _aware(end_at) or _aware(submission_deadline)

    if end is not None and current > end:
        return HackathonPhase.ENDED
    if start is not None and end is not None and start <= current <= end:
        return HackathonPhase.ONGOING
    if start is not None and current >= start and end is None:
        # Started with no end — treat as ongoing until we learn otherwise
        if reg_close is not None and current > reg_close:
            return HackathonPhase.ONGOING
        return HackathonPhase.ONGOING

    if reg_close is not None and current > reg_close:
        # Registration closed; event may not have started
        if start is not None and current < start:
            return HackathonPhase.UPCOMING
        if end is None and start is None:
            return HackathonPhase.ENDED
        return HackathonPhase.ENDED if end is None or current > end else HackathonPhase.ONGOING

    if reg_open is not None and current < reg_open:
        return HackathonPhase.UPCOMING

    if reg_close is not None and current <= reg_close:
        return HackathonPhase.OPEN

    if start is not None and current < start:
        return HackathonPhase.UPCOMING

    if reg_close is None and start is None and end is None:
        return HackathonPhase.UNKNOWN

    return HackathonPhase.OPEN if reg_close or reg_open else HackathonPhase.UNKNOWN


def registration_closes_in_days(
    registration_deadline: datetime | None,
    *,
    fallback_deadline: datetime | None = None,
    now: datetime | None = None,
) -> int | None:
    due = _aware(registration_deadline) or _aware(fallback_deadline)
    if due is None:
        return None
    current = _aware(now) or datetime.now(UTC)
    delta = due - current
    if delta.total_seconds() < 0:
        return None
    return max(0, int(delta.total_seconds() // 86400))
