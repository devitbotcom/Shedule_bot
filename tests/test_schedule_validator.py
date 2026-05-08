import calendar
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schedule_validator import validate_draft_grid

_MAPPING = {
    "scheduler_header_row": 1,
    "scheduler_date_column": "Day",
    "scheduler_day_type_column": "Day-type",
    "scheduler_department_columns": ["Surgery"],
    "date_column": "Day",
    "day_type_column": "Day-type",
    "department_columns": ["Surgery"],
}
_STAFF = [{"name": "Alice", "department": "Surgery"}]
_JUNE_MONTH, _JUNE_YEAR = 6, 2026   # June 1 = Monday; June 6 = Saturday


def _make_clean_grid(month_int: int, year_int: int) -> list[list]:
    """Header + all days with correct weekend marking."""
    rows = [["Day", "Day-type", "Surgery"]]
    for d in range(1, calendar.monthrange(year_int, month_int)[1] + 1):
        day_type = "holiday" if date(year_int, month_int, d).weekday() >= 5 else "labour"
        rows.append([str(d), day_type, ""])
    return rows


# ---------------------------------------------------------------------------
# T1 — no warnings for a valid grid
# ---------------------------------------------------------------------------

def test_no_warnings_valid_grid():
    grid = _make_clean_grid(_JUNE_MONTH, _JUNE_YEAR)
    assert validate_draft_grid(grid, _MAPPING, _STAFF, _JUNE_MONTH, _JUNE_YEAR) == []


# ---------------------------------------------------------------------------
# T2 — V1: empty staff for a department
# ---------------------------------------------------------------------------

def test_v1_empty_staff():
    grid = _make_clean_grid(_JUNE_MONTH, _JUNE_YEAR)
    warnings = validate_draft_grid(grid, _MAPPING, [], _JUNE_MONTH, _JUNE_YEAR)
    assert any("[Персонал]" in w and "Surgery" in w for w in warnings)


# ---------------------------------------------------------------------------
# T3 — V2: day number present, day-type empty
# ---------------------------------------------------------------------------

def test_v2_missing_day_type():
    grid = [["Day", "Day-type", "Surgery"], ["5", "", ""]]
    warnings = validate_draft_grid(grid, _MAPPING, _STAFF, _JUNE_MONTH, _JUNE_YEAR)
    assert any("[Структура]" in w and "5" in w for w in warnings)


# ---------------------------------------------------------------------------
# T4 — V3: empty day cell
# ---------------------------------------------------------------------------

def test_v3_empty_day_cell():
    grid = [["Day", "Day-type", "Surgery"], ["", "labour", ""]]
    warnings = validate_draft_grid(grid, _MAPPING, _STAFF, _JUNE_MONTH, _JUNE_YEAR)
    assert any("[Структура]" in w and "рядків без номера" in w for w in warnings)


# ---------------------------------------------------------------------------
# T5a — V4: February 2028 (leap, 29 days) — no V4 warning
# ---------------------------------------------------------------------------

def test_v4_leap_year_no_warning():
    grid = _make_clean_grid(2, 2028)   # 29 days
    warnings = validate_draft_grid(grid, _MAPPING, _STAFF, 2, 2028)
    assert not any("[Структура]" in w and "очікується" in w for w in warnings)


# ---------------------------------------------------------------------------
# T5b — V4: 29-row grid passed as February 2029 (non-leap, 28 days) — warns
# ---------------------------------------------------------------------------

def test_v4_non_leap_year_warns():
    grid = _make_clean_grid(2, 2028)   # 29 rows — but we tell validator it's 2029
    warnings = validate_draft_grid(grid, _MAPPING, _STAFF, 2, 2029)
    assert any("[Структура]" in w and "29" in w and "28" in w for w in warnings)


# ---------------------------------------------------------------------------
# T6 — V5: days out of order
# ---------------------------------------------------------------------------

def test_v5_days_out_of_order():
    grid = [
        ["Day", "Day-type", "Surgery"],
        ["1", "labour", ""],
        ["3", "labour", ""],
        ["2", "labour", ""],
    ]
    warnings = validate_draft_grid(grid, _MAPPING, _STAFF, _JUNE_MONTH, _JUNE_YEAR)
    assert any("[День 3]" in w and "порушено" in w and "2" in w for w in warnings)


# ---------------------------------------------------------------------------
# T7 — V6: Saturday marked labour
# ---------------------------------------------------------------------------

def test_v6_saturday_marked_labour():
    grid = [["Day", "Day-type", "Surgery"], ["6", "labour", ""]]  # June 6 = Saturday
    warnings = validate_draft_grid(grid, _MAPPING, _STAFF, _JUNE_MONTH, _JUNE_YEAR)
    assert any("[День 6]" in w and "субота" in w for w in warnings)


# ---------------------------------------------------------------------------
# T8 — V6: Saturday marked holiday — no false positive
# ---------------------------------------------------------------------------

def test_v6_saturday_marked_holiday_no_warning():
    grid = [["Day", "Day-type", "Surgery"], ["6", "holiday", ""]]  # June 6 = Saturday
    warnings = validate_draft_grid(grid, _MAPPING, _STAFF, _JUNE_MONTH, _JUNE_YEAR)
    assert not any("[День 6]" in w for w in warnings)


# ---------------------------------------------------------------------------
# T9 — AD-003: non-integer day cell skipped silently
# ---------------------------------------------------------------------------

def test_non_integer_day_skipped_silently():
    grid = [
        ["Day", "Day-type", "Surgery"],
        ["травень", "labour", ""],   # non-integer — skipped
        ["1", "labour", ""],
        ["2", "labour", ""],
    ]
    warnings = validate_draft_grid(grid, _MAPPING, _STAFF, _JUNE_MONTH, _JUNE_YEAR)
    assert not any("травень" in w for w in warnings)


# ---------------------------------------------------------------------------
# T13 — V6b: weekday marked holiday warns
# ---------------------------------------------------------------------------

def test_v6b_weekday_marked_holiday_warns():
    grid = [["Day", "Day-type", "Surgery"], ["2", "holiday", ""]]  # June 2 = Tuesday
    warnings = validate_draft_grid(grid, _MAPPING, _STAFF, _JUNE_MONTH, _JUNE_YEAR)
    assert any("[День 2]" in w and "вівторок" in w for w in warnings)


def test_v6b_weekday_marked_labour_no_warning():
    grid = [["Day", "Day-type", "Surgery"], ["2", "labour", ""]]  # June 2 = Tuesday
    warnings = validate_draft_grid(grid, _MAPPING, _STAFF, _JUNE_MONTH, _JUNE_YEAR)
    assert not any("[День 2]" in w for w in warnings)


# ---------------------------------------------------------------------------
# T14 — missing column diagnostic
# ---------------------------------------------------------------------------

def test_missing_date_column_warns():
    mapping = dict(_MAPPING)
    mapping["scheduler_date_column"] = "NonExistent"
    mapping["date_column"] = "NonExistent"
    grid = _make_clean_grid(_JUNE_MONTH, _JUNE_YEAR)
    warnings = validate_draft_grid(grid, mapping, _STAFF, _JUNE_MONTH, _JUNE_YEAR)
    assert any("[Налаштування]" in w and "NonExistent" in w and "scheduler_date_column" in w for w in warnings)


def test_missing_day_type_column_warns():
    mapping = dict(_MAPPING)
    mapping["scheduler_day_type_column"] = "NonExistent"
    mapping["day_type_column"] = "NonExistent"
    grid = _make_clean_grid(_JUNE_MONTH, _JUNE_YEAR)
    warnings = validate_draft_grid(grid, mapping, _STAFF, _JUNE_MONTH, _JUNE_YEAR)
    assert any("[Налаштування]" in w and "NonExistent" in w and "scheduler_day_type_column" in w for w in warnings)


# ---------------------------------------------------------------------------
# T15 — None cell value handled correctly (V2 fires even when gspread returns None)
# ---------------------------------------------------------------------------

def test_v2_fires_when_cell_is_none():
    grid = [["Day", "Day-type", "Surgery"], ["5", None, ""]]
    warnings = validate_draft_grid(grid, _MAPPING, _STAFF, _JUNE_MONTH, _JUNE_YEAR)
    assert any("[Структура]" in w and "5" in w for w in warnings)


# ---------------------------------------------------------------------------
# T10 — V7: empty name warns
# ---------------------------------------------------------------------------

def test_v7_empty_name_warns():
    staff = [{"name": "", "department": "Surgery"}]
    grid = _make_clean_grid(_JUNE_MONTH, _JUNE_YEAR)
    warnings = validate_draft_grid(grid, _MAPPING, staff, _JUNE_MONTH, _JUNE_YEAR)
    assert any("[Персонал]" in w and "порожнє ім'я" in w for w in warnings)


# ---------------------------------------------------------------------------
# T11 — V7: name with invalid characters warns
# ---------------------------------------------------------------------------

def test_v7_invalid_chars_warns():
    staff = [{"name": "Dr@Smith!", "department": "Surgery"}]
    grid = _make_clean_grid(_JUNE_MONTH, _JUNE_YEAR)
    warnings = validate_draft_grid(grid, _MAPPING, staff, _JUNE_MONTH, _JUNE_YEAR)
    assert any("[Персонал]" in w and "недопустимі символи" in w for w in warnings)


# ---------------------------------------------------------------------------
# T12 — V7: valid Ukrainian name — no false positive
# ---------------------------------------------------------------------------

def test_v7_ukrainian_name_no_warning():
    staff = [{"name": "Іваненко", "department": "Surgery"}]
    grid = _make_clean_grid(_JUNE_MONTH, _JUNE_YEAR)
    warnings = validate_draft_grid(grid, _MAPPING, staff, _JUNE_MONTH, _JUNE_YEAR)
    assert not any("[Персонал]" in w for w in warnings)


def test_v7_name_with_initials_no_warning():
    staff = [{"name": "Апкепон П. Е.", "department": "Surgery"}]
    grid = _make_clean_grid(_JUNE_MONTH, _JUNE_YEAR)
    warnings = validate_draft_grid(grid, _MAPPING, staff, _JUNE_MONTH, _JUNE_YEAR)
    assert not any("[Персонал]" in w for w in warnings)


def test_v7_double_dot_warns():
    staff = [{"name": "King D..", "department": "Surgery"}]
    grid = _make_clean_grid(_JUNE_MONTH, _JUNE_YEAR)
    warnings = validate_draft_grid(grid, _MAPPING, staff, _JUNE_MONTH, _JUNE_YEAR)
    assert any("[Персонал]" in w and "недопустимі символи" in w for w in warnings)


# ---------------------------------------------------------------------------
# C3 — year_int=None: V1/V2/V3/V5/V7 still run, V4/V6 skipped, no warning added
# ---------------------------------------------------------------------------

def test_c3_year_none_v1_still_runs():
    grid = _make_clean_grid(_JUNE_MONTH, _JUNE_YEAR)
    warnings = validate_draft_grid(grid, _MAPPING, [], _JUNE_MONTH, None)
    assert any("[Персонал]" in w and "Surgery" in w for w in warnings)


def test_c3_year_none_no_extra_warning():
    grid = _make_clean_grid(_JUNE_MONTH, _JUNE_YEAR)
    warnings = validate_draft_grid(grid, _MAPPING, _STAFF, _JUNE_MONTH, None)
    assert not any("рік" in w.lower() for w in warnings)


def test_c3_year_none_v4_not_in_warnings():
    grid = _make_clean_grid(_JUNE_MONTH, _JUNE_YEAR)
    warnings = validate_draft_grid(grid, _MAPPING, _STAFF, _JUNE_MONTH, None)
    assert not any("[Структура]" in w and "очікується" in w for w in warnings)


def test_c3_year_none_v6_not_in_warnings():
    grid = [["Day", "Day-type", "Surgery"], ["6", "labour", ""]]  # June 6 = Saturday
    warnings = validate_draft_grid(grid, _MAPPING, _STAFF, _JUNE_MONTH, None)
    assert not any("[День" in w for w in warnings)


def test_c3_year_none_no_crash():
    grid = _make_clean_grid(_JUNE_MONTH, _JUNE_YEAR)
    result = validate_draft_grid(grid, _MAPPING, _STAFF, _JUNE_MONTH, None)
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# C4 — missing date column: V3 does not cascade
# ---------------------------------------------------------------------------

def test_c4_missing_date_column_no_v3_cascade():
    mapping = dict(_MAPPING)
    mapping["scheduler_date_column"] = "NonExistent"
    mapping["date_column"] = "NonExistent"
    grid = _make_clean_grid(_JUNE_MONTH, _JUNE_YEAR)
    warnings = validate_draft_grid(grid, mapping, _STAFF, _JUNE_MONTH, _JUNE_YEAR)
    assert any("[Налаштування]" in w for w in warnings)
    assert not any("[Структура]" in w and "рядків без номера" in w for w in warnings)
