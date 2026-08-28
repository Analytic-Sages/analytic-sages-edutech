from __future__ import annotations

OFF_MISSION_TITLE_HINTS = (
    "account executive",
    "account director",
    "sales development",
    "sales manager",
    "head of sales",
    "recruiter",
    "talent acquisition",
    "customer success",
    "customer support",
    "people partner",
    "social media",
    "office manager",
    "marketing lead",
    "marketing manager",
    "lifecycle marketing",
    "hris",
    "technical sales",
)


def is_off_mission_title(title: str) -> bool:
    lowered = title.lower()
    # Sales, recruiting, and support stay out even when the title mentions intel or data.
    if any(hint in lowered for hint in OFF_MISSION_TITLE_HINTS):
        return True
    return False
