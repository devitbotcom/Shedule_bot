import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from main import _shift_time_to_server, run_gen_crontab, run_verify_cron


def _base_config():
    return {
        "XLSX_PATH": "/home/testuser/Shedule_bot/data/schedule.xlsx",
        "DB_PATH": "/home/testuser/Shedule_bot/data/shift_bot.db",
        "LOG_DIR": "/home/testuser/Shedule_bot/data/logs",
        "TELEGRAM_BOT_TOKEN": "fake-token",
        "TELEGRAM_GROUP_CHAT_ID": "-123",
    }


def _make_subprocess_result(stdout):
    m = MagicMock()
    m.stdout = stdout
    return m


# --- _shift_time_to_server (pure unit tests) ---

def test_labor_kyiv_to_server():
    assert _shift_time_to_server("17:00", 3, -4) == (10, 0)


def test_holiday_kyiv_to_server():
    assert _shift_time_to_server("09:00", 3, -4) == (2, 0)


def test_other_crosses_midnight():
    # 01:25 Kyiv − 7h = 18:25 server (previous calendar day)
    assert _shift_time_to_server("01:25", 3, -4) == (18, 25)


def test_same_timezone_no_offset():
    assert _shift_time_to_server("12:00", 0, 0) == (12, 0)


# --- run_gen_crontab ---

def _patch_gen_crontab(monkeypatch, server_stdout="-0400\n1000\n"):
    monkeypatch.setattr("main._shift_hours", lambda cfg: {"labor": "17:00", "holiday": "09:00", "other": "09:00"})
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: _make_subprocess_result(server_stdout),
    )


def test_gen_crontab_contains_all_shift_types(monkeypatch, capsys):
    _patch_gen_crontab(monkeypatch)
    with pytest.raises(SystemExit):
        run_gen_crontab(_base_config())
    out = capsys.readouterr().out
    assert "--shift-type labor" in out
    assert "--shift-type holiday" in out
    assert "--shift-type other" in out


def test_gen_crontab_contains_verify_entry(monkeypatch, capsys):
    _patch_gen_crontab(monkeypatch)
    with pytest.raises(SystemExit):
        run_gen_crontab(_base_config())
    out = capsys.readouterr().out
    assert "--verify-cron" in out
    assert "REMOVE AFTER FIRST FIRE" in out


def test_gen_crontab_install_path_from_xlsx(monkeypatch, capsys):
    _patch_gen_crontab(monkeypatch)
    with pytest.raises(SystemExit):
        run_gen_crontab(_base_config())
    out = capsys.readouterr().out
    assert "/home/testuser/Shedule_bot" in out


def test_gen_crontab_offset_failure_uses_placeholder(monkeypatch, capsys):
    monkeypatch.setattr("main._shift_hours", lambda cfg: {"labor": "17:00", "holiday": "09:00", "other": "09:00"})
    monkeypatch.setattr("subprocess.run", MagicMock(side_effect=Exception("subprocess failed")))
    with pytest.raises(SystemExit):
        run_gen_crontab(_base_config())
    out = capsys.readouterr().out
    assert "<MIN>" in out
    assert "<HOUR>" in out


def test_gen_crontab_contains_log_retention(monkeypatch, capsys):
    _patch_gen_crontab(monkeypatch)
    with pytest.raises(SystemExit):
        run_gen_crontab(_base_config())
    out = capsys.readouterr().out
    assert ".log" in out
    assert "mtime" in out


# --- run_verify_cron ---

def test_verify_cron_sends_to_group(monkeypatch):
    adapter_mock = MagicMock()
    monkeypatch.setattr("main.TelegramAdapter", lambda token: adapter_mock)
    with pytest.raises(SystemExit) as exc_info:
        run_verify_cron(_base_config())
    adapter_mock.send.assert_called_once()
    call_args = adapter_mock.send.call_args[0]
    assert call_args[0] == "-123"
    assert "✅" in call_args[1]
    assert exc_info.value.code == 0


def test_verify_cron_exits_1_on_send_failure(monkeypatch):
    adapter_mock = MagicMock()
    adapter_mock.send.side_effect = RuntimeError("Telegram unreachable")
    monkeypatch.setattr("main.TelegramAdapter", lambda token: adapter_mock)
    with pytest.raises(SystemExit) as exc_info:
        run_verify_cron(_base_config())
    assert exc_info.value.code == 1
