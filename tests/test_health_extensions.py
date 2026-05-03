import os
import subprocess
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from main import run_health


def _base_config():
    return {
        "XLSX_PATH": "/fake/data/schedule.xlsx",
        "DB_PATH": "/fake/data/shift_bot.db",
        "LOG_DIR": "/fake/data/logs",
        "TELEGRAM_BOT_TOKEN": "fake-token",
        "TELEGRAM_GROUP_CHAT_ID": "-123",
    }


def _patch_run_health_deps(monkeypatch):
    """Patch all run_health dependencies except the parts under test."""
    monkeypatch.setattr("main.init_db", lambda path: None)
    adapter_mock = MagicMock()
    adapter_mock.health_check.return_value = True
    monkeypatch.setattr("main.TelegramAdapter", lambda token: adapter_mock)
    monkeypatch.setattr("main.parse_schedule", lambda *a, **kw: [])
    monkeypatch.setattr("main.get_last_run_summary", lambda path: {"sent_at": None, "ok": 0, "fail": 0})
    monkeypatch.setattr("main.get_pending_count", lambda path, shifts: 0)


# --- D10: [SCHEDULE] ---

def test_schedule_line_shows_shift_hours(monkeypatch, capsys):
    _patch_run_health_deps(monkeypatch)
    monkeypatch.setattr("main._shift_hours", lambda cfg: {"labor": "17:00", "holiday": "09:00", "other": "08:20"})
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: MagicMock(stdout="Mon Jan  1 10:00:00 EDT 2026\n-0400\nEDT\n"))
    with pytest.raises(SystemExit):
        run_health(_base_config())
    out = capsys.readouterr().out
    assert "[SCHEDULE] shift_hours: labor=17:00  holiday=09:00  other=08:20" in out


def test_schedule_line_shows_error_when_mapping_unreadable(monkeypatch, capsys):
    _patch_run_health_deps(monkeypatch)
    monkeypatch.setattr("main._shift_hours", lambda cfg: (_ for _ in ()).throw(RuntimeError("file missing")))
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: MagicMock(stdout="Mon Jan  1 10:00:00 EDT 2026\n-0400\nEDT\n"))
    with pytest.raises(SystemExit):
        run_health(_base_config())
    out = capsys.readouterr().out
    assert "[SCHEDULE] ❌" in out


# --- D11: [ENV TIME] + [TZ OFFSET] ---

def _make_subprocess_result(stdout):
    m = MagicMock()
    m.stdout = stdout
    return m


def test_env_time_and_offset_shown(monkeypatch, capsys):
    _patch_run_health_deps(monkeypatch)
    monkeypatch.setattr("main._shift_hours", lambda cfg: {"labor": "17:00", "holiday": "09:00", "other": "08:20"})
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: _make_subprocess_result("Sun May  3 01:00:00 EDT 2026\n-0400\nEDT\n"),
    )
    with pytest.raises(SystemExit):
        run_health(_base_config())
    out = capsys.readouterr().out
    assert "[ENV TIME]  Sun May  3 01:00:00 EDT 2026" in out
    assert "[TZ OFFSET]" in out
    assert "EDT" in out


def test_env_time_shows_error_when_subprocess_fails(monkeypatch, capsys):
    _patch_run_health_deps(monkeypatch)
    monkeypatch.setattr("main._shift_hours", lambda cfg: {"labor": "17:00", "holiday": "09:00", "other": "08:20"})
    monkeypatch.setattr("subprocess.run", MagicMock(side_effect=Exception("subprocess failed")))
    with pytest.raises(SystemExit):
        run_health(_base_config())
    out = capsys.readouterr().out
    assert "[ENV TIME]  ❌" in out


def test_env_time_error_does_not_raise(monkeypatch):
    _patch_run_health_deps(monkeypatch)
    monkeypatch.setattr("main._shift_hours", lambda cfg: {"labor": "17:00", "holiday": "09:00", "other": "08:20"})
    monkeypatch.setattr("subprocess.run", MagicMock(side_effect=Exception("subprocess failed")))
    with pytest.raises(SystemExit):
        run_health(_base_config())  # must not raise anything other than SystemExit
