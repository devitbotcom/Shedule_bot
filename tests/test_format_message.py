import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import Shift, ShiftContext
from main import _format_message

HOURS = {"labor": "17:00", "holiday": "09:00", "other": "09:00"}


def make_shift(name, dept, day_type, date):
    return Shift(name, dept, day_type, date, "telegram", "-1001234567890")


def make_ctx(shift, prev=None, next_=None):
    return ShiftContext(shift=shift, prev_colleague=prev, next_colleague=next_)


def test_message_contains_employee_name():
    # Shift owner name must appear in the message
    ctx = make_ctx(make_shift("Іваненко О.В.", "Приймальне відділення", "labor", "2026-04-07"))
    assert "Іваненко О.В." in _format_message(ctx, HOURS)


def test_date_displayed_as_dd_mm_yyyy():
    # ISO date stored internally must be formatted as DD-MM-YYYY in the message
    ctx = make_ctx(make_shift("Alice", "Dept", "labor", "2026-04-07"))
    assert "07-04-2026" in _format_message(ctx, HOURS)


def test_prev_name_shown_when_present():
    # Previous colleague name must appear after 'замість'
    prev = make_shift("Петренко А.С.", "Dept", "labor", "2026-04-06")
    ctx = make_ctx(make_shift("Alice", "Dept", "labor", "2026-04-07"), prev=prev)
    assert "Петренко А.С." in _format_message(ctx, HOURS)


def test_prev_shown_as_dash_when_missing():
    # No previous colleague → '-' appears in message, line not omitted
    ctx = make_ctx(make_shift("Alice", "Dept", "labor", "2026-04-07"))
    msg = _format_message(ctx, HOURS)
    assert "замість -." in msg


def test_no_double_period_for_name_ending_with_period():
    # BUG-001: names ending with '.' (e.g. initials) must not produce double period
    prev = make_shift("Петренко А.С.", "Dept", "labor", "2026-04-06")
    ctx = make_ctx(make_shift("Alice", "Dept", "labor", "2026-04-07"), prev=prev)
    msg = _format_message(ctx, HOURS)
    assert "А.С.." not in msg
    assert "А.С." in msg


def test_next_line_shown_as_dash_when_missing():
    # No next colleague → 'Наступна зміна:' header still present, value is '-'
    ctx = make_ctx(make_shift("Alice", "Dept", "labor", "2026-04-07"))
    msg = _format_message(ctx, HOURS)
    assert "Наступна зміна:" in msg
    assert msg.strip().endswith("-")


def test_next_time_is_1700_for_labor():
    # Labor day next shift starts at 17:00
    ctx = make_ctx(
        make_shift("Alice", "Dept", "labor", "2026-04-07"),
        next_=make_shift("Bob", "Dept", "labor", "2026-04-08"),
    )
    assert "17:00" in _format_message(ctx, HOURS)


def test_next_time_is_0900_for_holiday():
    # Holiday next shift starts at 09:00
    ctx = make_ctx(
        make_shift("Alice", "Dept", "labor", "2026-04-07"),
        next_=make_shift("Bob", "Dept", "holiday", "2026-04-08"),
    )
    assert "09:00" in _format_message(ctx, HOURS)


def test_next_time_is_0900_for_other():
    # 'other' day type also starts at 09:00
    ctx = make_ctx(
        make_shift("Alice", "Dept", "labor", "2026-04-07"),
        next_=make_shift("Bob", "Dept", "other", "2026-04-08"),
    )
    assert "09:00" in _format_message(ctx, HOURS)


def test_custom_shift_hours_used():
    # IT overrides labor shift time to 16:00 — message must reflect the custom value
    custom_hours = {"labor": "16:00", "holiday": "08:00", "other": "08:00"}
    ctx = make_ctx(
        make_shift("Alice", "Dept", "labor", "2026-04-07"),
        next_=make_shift("Bob", "Dept", "labor", "2026-04-08"),
    )
    assert "16:00" in _format_message(ctx, custom_hours)
    assert "17:00" not in _format_message(ctx, custom_hours)


def test_full_message_structure():
    # Full message must match the expected template structure exactly
    shift = make_shift("Іваненко О.В.", "Dept", "labor", "2026-04-07")
    prev  = make_shift("Петренко А.С.", "Dept", "labor", "2026-04-06")
    next_ = make_shift("Сидоренко В.М.", "Dept", "labor", "2026-04-08")
    ctx = make_ctx(shift, prev=prev, next_=next_)
    msg = _format_message(ctx, HOURS)
    assert msg == (
        "Зміна: 07-04-2026\n"
        "Іваненко О.В. заступає на зміну замість Петренко А.С.\n"
        "\n"
        "Наступна зміна:\n"
        "08-04-2026 о 17:00 — Сидоренко В.М."
    )
