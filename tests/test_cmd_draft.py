"""
Unit tests for bot_hook._cmd_draft — internal logic and error paths.
All Google Sheets I/O is mocked; no network calls.
"""
import json
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bot_hook import _cmd_draft


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeSend:
    def __init__(self):
        self.calls: list[tuple] = []

    def __call__(self, token: str, chat_id: str, text: str) -> None:
        self.calls.append((token, chat_id, text))

    @property
    def last_text(self) -> str:
        return self.calls[-1][2] if self.calls else ""

    @property
    def count(self) -> int:
        return len(self.calls)


_MAPPING = {
    "header_row": 2,
    "date_column": "Date",
    "day_type_column": "Day-type",
    "department_columns": ["Surgery"],
    "shift_hours": {"labor": "17:00", "holiday": "09:00", "other": "09:00"},
    "scheduler_staff_tab": "Staff",
    "scheduler_schedule_tab": "Draft",
    "scheduler_output_tab": "Draft-by-bot",
    "scheduler_month_cell": "A1",
    "scheduler_year_cell": "B1",
}

_STAFF = [{"name": "Alice", "department": "Surgery"}]
_GRID = [
    ["червень", "2026", "", ""],
    ["Date", "Day-type", "Surgery"],
    ["2026-06-01", "labor", ""],
]


# ---------------------------------------------------------------------------
# Error path: missing env vars
# ---------------------------------------------------------------------------

def test_cmd_draft_missing_sheet_id(monkeypatch, tmp_path):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    monkeypatch.delenv("GOOGLE_SHEET_ID", raising=False)
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    _cmd_draft("T", "42")
    assert sent.count == 1
    assert "GOOGLE_SHEET_ID" in sent.last_text or "не налаштовано" in sent.last_text


def test_cmd_draft_missing_creds(monkeypatch, tmp_path):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    monkeypatch.setenv("GOOGLE_SHEET_ID", "sid")
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    _cmd_draft("T", "42")
    assert sent.count == 1
    assert "не налаштовано" in sent.last_text


# ---------------------------------------------------------------------------
# Error path: bad mapping file
# ---------------------------------------------------------------------------

def test_cmd_draft_missing_mapping_file(monkeypatch, tmp_path):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    monkeypatch.setenv("GOOGLE_SHEET_ID", "sid")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", "/creds.json")
    monkeypatch.setattr("bot_hook._ROOT", str(tmp_path))  # no data/schedule_mapping.json
    _cmd_draft("T", "42")
    assert sent.count == 1
    assert "schedule_mapping.json" in sent.last_text


# ---------------------------------------------------------------------------
# Error path: unrecognised month name
# ---------------------------------------------------------------------------

def test_cmd_draft_unknown_month(monkeypatch, tmp_path):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    monkeypatch.setenv("GOOGLE_SHEET_ID", "sid")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", "/creds.json")

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "schedule_mapping.json").write_text(json.dumps(_MAPPING), encoding="utf-8")
    monkeypatch.setattr("bot_hook._ROOT", str(tmp_path))

    monkeypatch.setattr("google_sheets_adapter.read_cell", lambda sid, tab, cell, creds: "january")
    _cmd_draft("T", "42")
    assert sent.count == 1
    assert "january" in sent.last_text or "місяця" in sent.last_text


# ---------------------------------------------------------------------------
# Error path: gspread read failure
# ---------------------------------------------------------------------------

def test_cmd_draft_gspread_read_failure(monkeypatch, tmp_path):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    monkeypatch.setenv("GOOGLE_SHEET_ID", "sid")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", "/creds.json")

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "schedule_mapping.json").write_text(json.dumps(_MAPPING), encoding="utf-8")
    monkeypatch.setattr("bot_hook._ROOT", str(tmp_path))

    monkeypatch.setattr("google_sheets_adapter.read_cell", lambda *a, **kw: (_ for _ in ()).throw(Exception("network error")))
    _cmd_draft("T", "42")
    assert sent.count == 1
    assert "Google Sheets" in sent.last_text


# ---------------------------------------------------------------------------
# Happy path: confirmation sent
# ---------------------------------------------------------------------------

def test_cmd_draft_happy_path(monkeypatch, tmp_path):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    monkeypatch.setenv("GOOGLE_SHEET_ID", "sid")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", "/creds.json")

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "schedule_mapping.json").write_text(json.dumps(_MAPPING), encoding="utf-8")
    monkeypatch.setattr("bot_hook._ROOT", str(tmp_path))

    monkeypatch.setattr("google_sheets_adapter.read_cell", lambda sid, tab, cell, creds: "червень" if cell == "A1" else "2026")
    monkeypatch.setattr("google_sheets_adapter.get_staff_list", lambda *a, **kw: _STAFF)
    monkeypatch.setattr("google_sheets_adapter.get_schedule_grid", lambda *a, **kw: _GRID)
    monkeypatch.setattr("google_sheets_adapter.write_schedule_grid", lambda *a, **kw: None)

    _cmd_draft("T", "42")
    assert sent.count == 1
    assert "✅" in sent.last_text
    assert "червень" in sent.last_text
    assert "2026" in sent.last_text
