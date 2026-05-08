from unittest.mock import MagicMock, patch

import gspread
import pytest

from google_sheets_adapter import (
    STAFF_DEPT_COL,
    STAFF_NAME_COL,
    _col_letter_to_index,
    get_schedule_grid,
    get_staff_list,
    read_cell,
    write_schedule_grid,
)


def _mock_gc(records=None, values=None):
    ws = MagicMock()
    ws.get_all_records.return_value = records if records is not None else []
    ws.get_all_values.return_value = values if values is not None else []
    gc = MagicMock()
    gc.open_by_key.return_value.worksheet.return_value = ws
    return gc


@patch("google_sheets_adapter.gspread.service_account")
def test_get_staff_list_returns_name_department_dicts(mock_sa):
    mock_sa.return_value = _mock_gc(values=[
        [STAFF_NAME_COL, STAFF_DEPT_COL],
        ["Alice", "Surgery"],
        ["Bob", "Anesthesia"],
    ])
    result = get_staff_list("sheet-id", "Staff", "/creds.json")
    assert result == [
        {"name": "Alice", "department": "Surgery", "preferred_days": [], "undesired_days": []},
        {"name": "Bob", "department": "Anesthesia", "preferred_days": [], "undesired_days": []},
    ]


@patch("google_sheets_adapter.gspread.service_account")
def test_get_staff_list_skips_rows_with_empty_name(mock_sa):
    mock_sa.return_value = _mock_gc(values=[
        [STAFF_NAME_COL, STAFF_DEPT_COL],
        ["Alice", "Surgery"],
        ["", ""],
    ])
    result = get_staff_list("sheet-id", "Staff", "/creds.json")
    assert len(result) == 1
    assert result[0]["name"] == "Alice"


# ---------------------------------------------------------------------------
# _col_letter_to_index helper
# ---------------------------------------------------------------------------

def test_col_letter_to_index_single():
    assert _col_letter_to_index("A") == 0
    assert _col_letter_to_index("B") == 1
    assert _col_letter_to_index("C") == 2
    assert _col_letter_to_index("Z") == 25


def test_col_letter_to_index_double():
    assert _col_letter_to_index("AA") == 26
    assert _col_letter_to_index("AB") == 27


def test_col_letter_to_index_lowercase():
    assert _col_letter_to_index("a") == 0
    assert _col_letter_to_index("c") == 2


def test_col_letter_to_index_a1_notation():
    assert _col_letter_to_index("A1") == 0
    assert _col_letter_to_index("C1") == 2
    assert _col_letter_to_index("D1") == 3
    assert _col_letter_to_index("AA1") == 26


# ---------------------------------------------------------------------------
# C7 — preference columns (column-letter addressing)
# ---------------------------------------------------------------------------

@patch("google_sheets_adapter.gspread.service_account")
def test_get_staff_list_parses_preferred_days(mock_sa):
    mock_sa.return_value = _mock_gc(values=[
        [STAFF_NAME_COL, STAFF_DEPT_COL, "preferred"],
        ["Alice", "Surgery", "1, 5, 15"],
    ])
    result = get_staff_list("sheet-id", "Staff", "/creds.json", preferred_col="C1")
    assert result[0]["preferred_days"] == [1, 5, 15]
    assert result[0]["undesired_days"] == []


@patch("google_sheets_adapter.gspread.service_account")
def test_get_staff_list_parses_undesired_days(mock_sa):
    mock_sa.return_value = _mock_gc(values=[
        [STAFF_NAME_COL, STAFF_DEPT_COL, "", "undesired"],
        ["Alice", "Surgery", "", "10, 20"],
    ])
    result = get_staff_list("sheet-id", "Staff", "/creds.json", undesired_col="D1")
    assert result[0]["undesired_days"] == [10, 20]
    assert result[0]["preferred_days"] == []


@patch("google_sheets_adapter.gspread.service_account")
def test_get_staff_list_missing_preference_column_returns_empty_lists(mock_sa):
    # Row only has 2 columns; C (idx 2) and D (idx 3) are out of range → empty lists
    mock_sa.return_value = _mock_gc(values=[
        [STAFF_NAME_COL, STAFF_DEPT_COL],
        ["Alice", "Surgery"],
    ])
    result = get_staff_list("sheet-id", "Staff", "/creds.json",
                            preferred_col="C1", undesired_col="D1")
    assert result[0]["preferred_days"] == []
    assert result[0]["undesired_days"] == []


@patch("google_sheets_adapter.gspread.service_account")
def test_get_staff_list_empty_preference_cell_returns_empty_lists(mock_sa):
    mock_sa.return_value = _mock_gc(values=[
        [STAFF_NAME_COL, STAFF_DEPT_COL, "", ""],
        ["Alice", "Surgery", "", ""],
    ])
    result = get_staff_list("sheet-id", "Staff", "/creds.json",
                            preferred_col="C1", undesired_col="D1")
    assert result[0]["preferred_days"] == []
    assert result[0]["undesired_days"] == []


@patch("google_sheets_adapter.gspread.service_account")
def test_get_staff_list_empty_sheet(mock_sa):
    mock_sa.return_value = _mock_gc(values=[])
    assert get_staff_list("sheet-id", "Staff", "/creds.json") == []


@patch("google_sheets_adapter.gspread.service_account")
def test_get_schedule_grid_returns_2d_list(mock_sa):
    grid = [
        ["", "", "Surgery", "Anesthesia"],
        ["2026-05-01", "labor", "Alice", "Bob"],
    ]
    mock_sa.return_value = _mock_gc(values=grid)
    result = get_schedule_grid("sheet-id", "Schedule", "/creds.json")
    assert result == grid


@patch("google_sheets_adapter.gspread.service_account")
def test_get_schedule_grid_empty_sheet(mock_sa):
    mock_sa.return_value = _mock_gc(values=[])
    assert get_schedule_grid("sheet-id", "Schedule", "/creds.json") == []


@patch("google_sheets_adapter.gspread.service_account")
def test_adapter_uses_credentials_path(mock_sa):
    mock_sa.return_value = _mock_gc(records=[])
    get_staff_list("sid", "Staff", "/my/service_account.json")
    mock_sa.assert_called_once_with(filename="/my/service_account.json")


@patch("google_sheets_adapter.gspread.service_account")
def test_adapter_opens_correct_sheet_and_tab(mock_sa):
    gc = _mock_gc(values=[])
    mock_sa.return_value = gc
    get_schedule_grid("my-sheet-id", "MyTab", "/creds.json")
    gc.open_by_key.assert_called_once_with("my-sheet-id")
    gc.open_by_key.return_value.worksheet.assert_called_once_with("MyTab")


@patch("google_sheets_adapter.gspread.service_account")
def test_read_cell_returns_string_value(mock_sa):
    ws = MagicMock()
    ws.acell.return_value.value = "червень"
    gc = MagicMock()
    gc.open_by_key.return_value.worksheet.return_value = ws
    mock_sa.return_value = gc
    result = read_cell("sheet-id", "Draft", "A1", "/creds.json")
    assert result == "червень"
    ws.acell.assert_called_once_with("A1")


@patch("google_sheets_adapter.gspread.service_account")
def test_write_schedule_grid_overwrites_existing_tab(mock_sa):
    ws = MagicMock()
    spreadsheet = MagicMock()
    spreadsheet.worksheet.return_value = ws
    gc = MagicMock()
    gc.open_by_key.return_value = spreadsheet
    mock_sa.return_value = gc
    rows = [["a", "b"], ["c", "d"]]
    write_schedule_grid("sheet-id", "Draft-by-bot", rows, "/creds.json")
    ws.clear.assert_called_once()
    ws.update.assert_called_once_with(rows)


@patch("google_sheets_adapter.gspread.service_account")
def test_write_schedule_grid_creates_tab_if_absent(mock_sa):
    new_ws = MagicMock()
    spreadsheet = MagicMock()
    spreadsheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound("Draft-by-bot")
    spreadsheet.add_worksheet.return_value = new_ws
    gc = MagicMock()
    gc.open_by_key.return_value = spreadsheet
    mock_sa.return_value = gc
    rows = [["x", "y"]]
    write_schedule_grid("sheet-id", "Draft-by-bot", rows, "/creds.json")
    spreadsheet.add_worksheet.assert_called_once()
    new_ws.update.assert_called_once_with(rows)
