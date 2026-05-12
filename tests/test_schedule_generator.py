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
    result, _ = generate_schedule(staff, _GRID, _MAPPING)
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
    result, _ = generate_schedule(staff, grid, mapping)
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
    result, _ = generate_schedule(staff, grid, mapping)
    assert result[1][2] == "Alice"
    assert result[2][2] == ""   # empty row untouched
    assert result[3][2] == "Alice"


def test_generate_empty_grid_returns_empty():
    result, warnings = generate_schedule([], [], _MAPPING)
    assert result == [] and warnings == []


def test_generate_unknown_department_column_no_crash():
    staff = [{"name": "Alice", "department": "Surgery"}]
    grid = [
        ["Date", "Day-type", "Surgery"],
        ["2026-06-01", "labor", ""],
    ]
    mapping = {"header_row": 1, "day_type_column": "Day-type", "department_columns": ["Surgery", "Unknown"]}
    result, _ = generate_schedule(staff, grid, mapping)
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
    result, _ = generate_schedule(staff, grid, mapping)
    assert result[1][2] == "Alice"


def test_scheduler_keys_absent_falls_back_to_shared():
    staff = [{"name": "Alice", "department": "Surgery"}]
    grid = [
        ["Date", "Day-type", "Surgery"],
        ["2026-06-01", "labor", ""],
    ]
    mapping = {"header_row": 1, "day_type_column": "Day-type", "department_columns": ["Surgery"]}
    result, _ = generate_schedule(staff, grid, mapping)
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
    result, _ = generate_schedule(staff, grid, _PREF_MAPPING)
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
    result, _ = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[2][2] == "Bob"    # Bob has lower count → chosen


def test_c1_unknown_prefill_name_no_crash():
    staff = [{"name": "Alice", "department": "Surgery"}]
    grid = [
        ["Day", "Day-type", "Surgery"],
        ["1", "labour", "UnknownPerson"],  # not in staff list
        ["2", "labour", ""],
    ]
    result, _ = generate_schedule(staff, grid, _PREF_MAPPING)
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
    result, _ = generate_schedule(staff, grid, _PREF_MAPPING)
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
    result, _ = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[1][2] == "Bob"


def test_c8_all_undesired_slot_empty_with_warning():
    """Both candidates mark day 3 as undesired — slot left empty + warning."""
    staff = [
        {"name": "Alice", "department": "Surgery", "preferred_days": [], "undesired_days": [3]},
        {"name": "Bob",   "department": "Surgery", "preferred_days": [], "undesired_days": [3]},
    ]
    grid = [
        ["Day", "Day-type", "Surgery"],
        ["3", "labour", ""],
    ]
    result, warnings = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[1][2] == ""
    assert any("[Персонал]" in w and "конфліктна дата" in w for w in warnings)


# ---------------------------------------------------------------------------
# C9 — no-consecutive-day hard constraint
# ---------------------------------------------------------------------------

def test_c9_consecutive_avoided():
    """Alice assigned day 1 → not assigned day 2 when Bob available."""
    staff = [
        {"name": "Alice", "department": "Surgery", "preferred_days": [], "undesired_days": []},
        {"name": "Bob",   "department": "Surgery", "preferred_days": [], "undesired_days": []},
    ]
    grid = [
        ["Day", "Day-type", "Surgery"],
        ["1", "labour", ""],
        ["2", "labour", ""],
    ]
    result, _ = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[1][2] != result[2][2]   # different person each day


def test_c9_all_worked_yesterday_slot_empty():
    """Only Alice in dept, worked day 1 → day 2 slot left empty + warning."""
    staff = [
        {"name": "Alice", "department": "Surgery", "preferred_days": [], "undesired_days": []},
    ]
    grid = [
        ["Day", "Day-type", "Surgery"],
        ["1", "labour", ""],
        ["2", "labour", ""],
    ]
    result, warnings = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[2][2] == ""
    assert any("[День 2]" in w and "вчора" in w for w in warnings)


def test_c9_day1_no_consecutive_penalty():
    """Day 1: last_day empty → no penalty, slot filled normally."""
    staff = [
        {"name": "Alice", "department": "Surgery", "preferred_days": [], "undesired_days": []},
    ]
    grid = [
        ["Day", "Day-type", "Surgery"],
        ["1", "labour", ""],
    ]
    result, warnings = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[1][2] == "Alice"
    assert not any("вчора" in w for w in warnings)


def test_c9_returns_tuple():
    """generate_schedule always returns a (grid, warnings) tuple."""
    output = generate_schedule([], [], _MAPPING)
    assert isinstance(output, tuple) and len(output) == 2


# ---------------------------------------------------------------------------
# V8 — inline exclusion of candidates with conflicting preference for a day
# ---------------------------------------------------------------------------

def test_v8_conflicted_person_excluded_bob_assigned():
    """Alice has day 1 in both lists → excluded; Bob assigned instead."""
    staff = [
        {"name": "Alice", "department": "Surgery", "preferred_days": [1], "undesired_days": [1]},
        {"name": "Bob",   "department": "Surgery", "preferred_days": [],  "undesired_days": []},
    ]
    grid = [["Day", "Day-type", "Surgery"], ["1", "labour", ""]]
    result, _ = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[1][2] == "Bob"


def test_v8_conflicted_person_excluded_only_on_conflict_day():
    """Alice excluded on day 1 (conflict); both eligible on day 2."""
    staff = [
        {"name": "Alice", "department": "Surgery", "preferred_days": [1], "undesired_days": [1]},
        {"name": "Bob",   "department": "Surgery", "preferred_days": [],  "undesired_days": []},
    ]
    grid = [
        ["Day", "Day-type", "Surgery"],
        ["1", "labour", ""],
        ["2", "labour", ""],
    ]
    result, _ = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[1][2] == "Bob"   # Alice excluded on day 1
    assert result[2][2] != ""      # both eligible on day 2


def test_v8_all_conflicted_slot_empty_with_warning():
    """Only Alice in dept; V8 conflict on day 1 → slot empty + warning."""
    staff = [
        {"name": "Alice", "department": "Surgery", "preferred_days": [1], "undesired_days": [1]},
    ]
    grid = [["Day", "Day-type", "Surgery"], ["1", "labour", ""]]
    result, warnings = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[1][2] == ""
    assert any("[Персонал]" in w and "конфліктна дата" in w for w in warnings)


# ---------------------------------------------------------------------------
# V10 — skip preference tiers when all eligible candidates prefer the same day
# ---------------------------------------------------------------------------

def test_v10_all_prefer_same_day_slot_empty_with_warning():
    """All staff prefer day 1 → slot left empty + warning."""
    staff = [
        {"name": "Alice", "department": "Surgery", "preferred_days": [1], "undesired_days": []},
        {"name": "Bob",   "department": "Surgery", "preferred_days": [1], "undesired_days": []},
    ]
    grid = [["Day", "Day-type", "Surgery"], ["1", "labour", ""]]
    result, warnings = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[1][2] == ""
    assert any("[Персонал]" in w and "Surgery" in w and "день 1" in w
               and "конфліктна дата" in w for w in warnings)


def test_v10_not_all_prefer_same_day_no_false_positive():
    """Only Alice prefers day 1 (Bob neutral) → no V10 warning; Alice assigned."""
    staff = [
        {"name": "Alice", "department": "Surgery", "preferred_days": [1], "undesired_days": []},
        {"name": "Bob",   "department": "Surgery", "preferred_days": [],  "undesired_days": []},
    ]
    grid = [["Day", "Day-type", "Surgery"], ["1", "labour", ""]]
    result, warnings = generate_schedule(staff, grid, _PREF_MAPPING)
    assert result[1][2] == "Alice"
    assert not any("перевага не застосовується" in w for w in warnings)
