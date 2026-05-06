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
