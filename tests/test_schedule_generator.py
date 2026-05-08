import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schedule_generator import UA_MONTHS, generate_schedule

_MAPPING = {
    "header_row": 2,
    "day_type_column": "Day-type",
    "department_columns": ["Surgery", "Anesthesia"],
}

_GRID = [
    ["", "", "", ""],
    ["Date", "Day-type", "Surgery", "Anesthesia"],
    ["2026-06-01", "labor", "", ""],
    ["2026-06-02", "holiday", "", ""],
]


def test_ua_months_complete():
    assert len(UA_MONTHS) == 12
    assert UA_MONTHS["січень"] == 1
    assert UA_MONTHS["грудень"] == 12


def test_generate_assigns_staff_to_departments():
    staff = [
        {"name": "Alice", "department": "Surgery"},
        {"name": "Bob", "department": "Surgery"},
        {"name": "Carol", "department": "Anesthesia"},
    ]
    result = generate_schedule(staff, _GRID, _MAPPING)
    assert result[2][2] != ""   # Surgery day 1 filled
    assert result[2][3] == "Carol"  # Anesthesia day 1
    assert result[3][2] != ""   # Surgery day 2 filled
    assert result[3][3] == "Carol"  # Anesthesia day 2 (only one)


def test_generate_round_robin_distributes_evenly():
    staff = [
        {"name": "Alice", "department": "Surgery"},
        {"name": "Bob", "department": "Surgery"},
    ]
    grid = [
        ["Date", "Day-type", "Surgery"],
        ["2026-06-01", "labor", ""],
        ["2026-06-02", "labor", ""],
        ["2026-06-03", "labor", ""],
        ["2026-06-04", "labor", ""],
    ]
    mapping = {"header_row": 1, "day_type_column": "Day-type", "department_columns": ["Surgery"]}
    result = generate_schedule(staff, grid, mapping)
    names = [result[i][2] for i in range(1, 5)]
    assert names.count("Alice") == 2
    assert names.count("Bob") == 2


def test_generate_skips_rows_with_empty_day_type():
    staff = [{"name": "Alice", "department": "Surgery"}]
    grid = [
        ["Date", "Day-type", "Surgery"],
        ["2026-06-01", "labor", ""],
        ["", "", ""],
        ["2026-06-03", "holiday", ""],
    ]
    mapping = {"header_row": 1, "day_type_column": "Day-type", "department_columns": ["Surgery"]}
    result = generate_schedule(staff, grid, mapping)
    assert result[1][2] == "Alice"
    assert result[2][2] == ""   # empty row untouched
    assert result[3][2] == "Alice"


def test_generate_empty_grid_returns_empty():
    assert generate_schedule([], [], _MAPPING) == []


def test_generate_unknown_department_column_no_crash():
    staff = [{"name": "Alice", "department": "Surgery"}]
    grid = [
        ["Date", "Day-type", "Surgery"],
        ["2026-06-01", "labor", ""],
    ]
    mapping = {"header_row": 1, "day_type_column": "Day-type", "department_columns": ["Surgery", "Unknown"]}
    result = generate_schedule(staff, grid, mapping)
    assert result[1][2] == "Alice"


def test_scheduler_keys_override_shared_keys():
    staff = [{"name": "Alice", "department": "Surgery"}]
    grid = [
        ["Date", "Day-type", "Surgery"],
        ["2026-06-01", "labor", ""],
    ]
    mapping = {
        "header_row": 99,           # wrong — should be ignored
        "day_type_column": "WRONG",
        "department_columns": ["WRONG"],
        "scheduler_header_row": 1,
        "scheduler_day_type_column": "Day-type",
        "scheduler_department_columns": ["Surgery"],
    }
    result = generate_schedule(staff, grid, mapping)
    assert result[1][2] == "Alice"


def test_scheduler_keys_absent_falls_back_to_shared():
    staff = [{"name": "Alice", "department": "Surgery"}]
    grid = [
        ["Date", "Day-type", "Surgery"],
        ["2026-06-01", "labor", ""],
    ]
    mapping = {"header_row": 1, "day_type_column": "Day-type", "department_columns": ["Surgery"]}
    result = generate_schedule(staff, grid, mapping)
    assert result[1][2] == "Alice"


def test_generate_does_not_mutate_input():
    staff = [{"name": "Alice", "department": "Surgery"}]
    grid = [
        ["Date", "Day-type", "Surgery"],
        ["2026-06-01", "labor", ""],
    ]
    mapping = {"header_row": 1, "day_type_column": "Day-type", "department_columns": ["Surgery"]}
    original_cell = grid[1][2]
    generate_schedule(staff, grid, mapping)
    assert grid[1][2] == original_cell  # input grid not mutated


# ---------------------------------------------------------------------------
# C1 — pre-filled cells: skip + count toward balance
# ---------------------------------------------------------------------------

_PREF_MAPPING = {
    "header_row": 1,
    "day_type_column": "Day-type",
    "department_columns": ["Surgery"],
    "date_column": "Day",
}


def test_c1_prefilled_cell_not_overwritten():
    staff = [{"name": "Alice", "department": "Surgery"},
             {"name": "Bob", "department": "Surgery"}]
    grid = [
        ["Day", "Day-type", "Surgery"],
        ["1", "labour", "Alice"],   # pre-filled
        ["2", "labour", ""],
    ]
    result = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[1][2] == "Alice"   # pre-fill preserved


def test_c1_prefilled_counted_in_balance():
    """Pre-filled Alice on day 1 → Bob assigned on day 2 (balance corrected)."""
    staff = [{"name": "Alice", "department": "Surgery"},
             {"name": "Bob", "department": "Surgery"}]
    grid = [
        ["Day", "Day-type", "Surgery"],
        ["1", "labour", "Alice"],   # Alice pre-filled (count=1)
        ["2", "labour", ""],
    ]
    result = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[2][2] == "Bob"    # Bob has lower count → chosen


def test_c1_unknown_prefill_name_no_crash():
    staff = [{"name": "Alice", "department": "Surgery"}]
    grid = [
        ["Day", "Day-type", "Surgery"],
        ["1", "labour", "UnknownPerson"],  # not in staff list
        ["2", "labour", ""],
    ]
    result = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[1][2] == "UnknownPerson"   # unchanged
    assert result[2][2] == "Alice"           # Alice still assigned


# ---------------------------------------------------------------------------
# C8 — preference-aware slot selection
# ---------------------------------------------------------------------------

def test_c8_preferred_assigned_before_neutral():
    """Alice prefers day 1, Bob is neutral → Alice assigned on day 1."""
    staff = [
        {"name": "Alice", "department": "Surgery", "preferred_days": [1], "undesired_days": []},
        {"name": "Bob",   "department": "Surgery", "preferred_days": [],  "undesired_days": []},
    ]
    grid = [
        ["Day", "Day-type", "Surgery"],
        ["1", "labour", ""],
    ]
    result = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[1][2] == "Alice"


def test_c8_neutral_assigned_before_undesired():
    """Bob is neutral, Alice has day 2 as undesired → Bob assigned on day 2."""
    staff = [
        {"name": "Alice", "department": "Surgery", "preferred_days": [],  "undesired_days": [2]},
        {"name": "Bob",   "department": "Surgery", "preferred_days": [],  "undesired_days": []},
    ]
    grid = [
        ["Day", "Day-type", "Surgery"],
        ["2", "labour", ""],
    ]
    result = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[1][2] == "Bob"


def test_c8_all_undesired_slot_still_filled():
    """Both candidates mark day 3 as undesired — slot still filled (soft constraint)."""
    staff = [
        {"name": "Alice", "department": "Surgery", "preferred_days": [], "undesired_days": [3]},
        {"name": "Bob",   "department": "Surgery", "preferred_days": [], "undesired_days": [3]},
    ]
    grid = [
        ["Day", "Day-type", "Surgery"],
        ["3", "labour", ""],
    ]
    result = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[1][2] in ("Alice", "Bob")   # someone assigned
