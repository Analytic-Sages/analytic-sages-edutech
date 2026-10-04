"""Minimal iCalendar (RFC 5545) serialiser for the classroom subscribe feed.

Only the subset we need: VCALENDAR wrapping VEVENTs, each with a VALARM reminder,
all timestamps in UTC. Kept dependency-free and pure so it is easy to unit test.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone

# Default pop-up reminder before a session starts.
REMINDER_MINUTES = 15
PRODID = "-//Analytic Sages//Classroom//EN"


@dataclass(frozen=True)
class CalendarEvent:
    uid: str
    starts_at: datetime
    ends_at: datetime
    summary: str
    description: str = ""
    location: str = ""


def ics_utc(value: datetime) -> str:
    """UTC basic-format timestamp, e.g. 20261005T170000Z."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> list[str]:
    """Fold long content lines to the 75-octet limit required by RFC 5545."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return [line]
    chunks: list[str] = []
    current = line
    while len(current.encode("utf-8")) > 75:
        cut = 75
        while len(current[:cut].encode("utf-8")) > 75:
            cut -= 1
        chunks.append(current[:cut])
        current = " " + current[cut:]
    chunks.append(current)
    return chunks


def _event_lines(event: CalendarEvent, *, stamp: str) -> list[str]:
    lines = [
        "BEGIN:VEVENT",
        f"UID:{event.uid}",
        f"DTSTAMP:{stamp}",
        f"DTSTART:{ics_utc(event.starts_at)}",
        f"DTEND:{ics_utc(event.ends_at)}",
        f"SUMMARY:{_escape(event.summary)}",
    ]
    if event.description:
        lines.append(f"DESCRIPTION:{_escape(event.description)}")
    if event.location:
        lines.append(f"LOCATION:{_escape(event.location)}")
    lines += [
        "BEGIN:VALARM",
        f"TRIGGER:-PT{REMINDER_MINUTES}M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:{_escape(event.summary)}",
        "END:VALARM",
        "END:VEVENT",
    ]
    return lines


def build_calendar(
    events: Iterable[CalendarEvent], *, calendar_name: str = "Analytic Sages Classroom"
) -> str:
    stamp = ics_utc(datetime.now(timezone.utc))
    raw = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(calendar_name)}",
        "X-PUBLISHED-TTL:PT1H",
    ]
    for event in events:
        raw.extend(_event_lines(event, stamp=stamp))
    raw.append("END:VCALENDAR")

    folded: list[str] = []
    for line in raw:
        folded.extend(_fold(line))
    return "\r\n".join(folded) + "\r\n"