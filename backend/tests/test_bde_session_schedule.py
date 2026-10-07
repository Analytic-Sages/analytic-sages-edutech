from __future__ import annotations

from collections import Counter
from datetime import date

import pytest

from app.models.classroom import LiveSessionType
from app.services.seed_bde_classroom import (
    OFFICE_HOUR_WEEKDAY,
    PROGRAM_START_DATE,
    SESSIONS_PER_WEEK,
    TOTAL_TEACHING_SESSIONS,
    TOTAL_WEEKS,
    WAT,
    bde_session_schedule,
)


def test_schedule_has_20_teaching_sessions_and_10_office_hours():
    schedule = bde_session_schedule()
    counts = Counter(item.session_type for item in schedule)
    assert counts[LiveSessionType.TEACHING] == TOTAL_TEACHING_SESSIONS == 20
    assert counts[LiveSessionType.OFFICE_HOUR] == TOTAL_WEEKS == 10
    assert len(schedule) == 30


def test_teaching_numbers_are_unique_one_to_twenty():
    teaching = [s for s in bde_session_schedule() if s.session_type is LiveSessionType.TEACHING]
    assert sorted(s.session_number for s in teaching) == list(range(1, 21))
    assert len({s.starts_at for s in teaching}) == 20


def test_teaching_days_are_monday_and_wednesday():
    teaching = [s for s in bde_session_schedule() if s.session_type is LiveSessionType.TEACHING]
    weekdays = {s.starts_at.astimezone(WAT).weekday() for s in teaching}
    assert weekdays == {0, 2}
    for week_index in range(TOTAL_WEEKS):
        chunk = teaching[week_index * SESSIONS_PER_WEEK : (week_index + 1) * SESSIONS_PER_WEEK]
        assert [s.starts_at.astimezone(WAT).weekday() for s in chunk] == [0, 2]


def test_office_hours_are_fridays():
    office = [s for s in bde_session_schedule() if s.session_type is LiveSessionType.OFFICE_HOUR]
    assert {s.starts_at.astimezone(WAT).weekday() for s in office} == {OFFICE_HOUR_WEEKDAY}
    assert sorted(s.session_number for s in office) == list(range(1, 11))


def test_first_session_is_monday_5_october_2026_at_18_wat():
    schedule = bde_session_schedule()
    first = min(schedule, key=lambda s: s.starts_at)
    local = first.starts_at.astimezone(WAT)
    assert local.strftime("%Y-%m-%d %H:%M") == "2026-10-05 18:00"
    assert local.weekday() == 0
    # Stored in UTC (+1 offset), matching the existing classroom convention.
    assert first.starts_at.isoformat() == "2026-10-05T17:00:00+00:00"


def test_teaching_is_four_hours_and_office_hour_is_three():
    schedule = bde_session_schedule()
    teaching = next(s for s in schedule if s.session_type is LiveSessionType.TEACHING)
    office = next(s for s in schedule if s.session_type is LiveSessionType.OFFICE_HOUR)
    assert (teaching.ends_at - teaching.starts_at).total_seconds() == 4 * 3600
    assert (office.ends_at - office.starts_at).total_seconds() == 3 * 3600


def test_each_teaching_session_carries_its_summary_and_week_objectives():
    teaching = next(s for s in bde_session_schedule() if s.session_type is LiveSessionType.TEACHING)
    assert teaching.session_number == 1
    # First objective is the session-specific summary, then the week objectives.
    assert teaching.objectives[0].startswith("Map the full path")
    assert len(teaching.objectives) == 4


def test_start_date_must_be_a_monday():
    with pytest.raises(ValueError):
        bde_session_schedule(date(2026, 10, 6))


def test_default_start_is_program_start_monday():
    assert PROGRAM_START_DATE.weekday() == 0