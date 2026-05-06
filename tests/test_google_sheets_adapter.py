from unittest.mock import MagicMock, patch

import pytest

from google_sheets_adapter import (
    STAFF_DEPT_COL,
    STAFF_NAME_COL,
    get_schedule_grid,
    get_staff_list,
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
    mock_sa.return_value = _mock_gc(records=[
        {STAFF_NAME_COL: "Alice", STAFF_DEPT_COL: "Surgery"},
        {STAFF_NAME_COL: "Bob", STAFF_DEPT_COL: "Anesthesia"},
    ])
    result = get_staff_list("sheet-id", "Staff", "/creds.json")
    assert result == [
        {"name": "Alice", "department": "Surgery"},
        {"name": "Bob", "department": "Anesthesia"},
    ]


@patch("google_sheets_adapter.gspread.service_account")
def test_get_staff_list_skips_rows_with_empty_name(mock_sa):
    mock_sa.return_value = _mock_gc(records=[
        {STAFF_NAME_COL: "Alice", STAFF_DEPT_COL: "Surgery"},
        {STAFF_NAME_COL: "", STAFF_DEPT_COL: ""},
    ])
    result = get_staff_list("sheet-id", "Staff", "/creds.json")
    assert len(result) == 1
    assert result[0]["name"] == "Alice"


@patch("google_sheets_adapter.gspread.service_account")
def test_get_staff_list_empty_sheet(mock_sa):
    mock_sa.return_value = _mock_gc(records=[])
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
