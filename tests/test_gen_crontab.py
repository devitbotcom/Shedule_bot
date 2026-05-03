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


class _CrontabCapture:
    """Routes subprocess.run calls: bash offset query → server_stdout; crontab -l → existing_crontab; crontab - → captures input."""

    def __init__(self, server_stdout="-0400\n1000\n", existing_crontab=""):
        self.server_stdout = server_stdout
        self.existing_crontab = existing_crontab
        self.installed = ""

    def run(self, args, **kw):
        m = MagicMock()
        m.returncode = 0
        if isinstance(args, list) and args[0] == "crontab":
            if "-l" in args:
                m.stdout = self.existing_crontab
            else:
                self.installed = kw.get("input", "")
        else:
            m.stdout = self.server_stdout
        return m


def _patch_gen_crontab(monkeypatch, server_stdout="-0400\n1000\n", existing_crontab=""):
    cap = _CrontabCapture(server_stdout, existing_crontab)
    monkeypatch.setattr("main._shift_hours", lambda cfg: {"labor": "17:00", "holiday": "09:00", "other": "09:00"})
    monkeypatch.setattr("subprocess.run", cap.run)
    return cap


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

def test_gen_crontab_contains_all_shift_types(monkeypatch):
    cap = _patch_gen_crontab(monkeypatch)
    with pytest.raises(SystemExit):
        run_gen_crontab(_base_config())
    assert "--shift-type labor" in cap.installed
    assert "--shift-type holiday" in cap.installed
    assert "--shift-type other" in cap.installed


def test_gen_crontab_contains_verify_entry(monkeypatch):
    cap = _patch_gen_crontab(monkeypatch)
    with pytest.raises(SystemExit):
        run_gen_crontab(_base_config())
    assert "--verify-cron" in cap.installed


def test_gen_crontab_install_path_from_xlsx(monkeypatch):
    cap = _patch_gen_crontab(monkeypatch)
    with pytest.raises(SystemExit):
        run_gen_crontab(_base_config())
    assert "/home/testuser/Shedule_bot" in cap.installed


def test_gen_crontab_offset_failure_uses_placeholder(monkeypatch, capsys):
    monkeypatch.setattr("main._shift_hours", lambda cfg: {"labor": "17:00", "holiday": "09:00", "other": "09:00"})
    monkeypatch.setattr("subprocess.run", MagicMock(side_effect=Exception("subprocess failed")))
    with pytest.raises(SystemExit):
        run_gen_crontab(_base_config())
    out = capsys.readouterr().out
    assert "<MIN>" in out
    assert "<HOUR>" in out


def test_gen_crontab_contains_log_retention(monkeypatch):
    cap = _patch_gen_crontab(monkeypatch)
    with pytest.raises(SystemExit):
        run_gen_crontab(_base_config())
    assert ".log" in cap.installed
    assert "mtime" in cap.installed


def test_gen_crontab_installs_via_crontab(monkeypatch):
    cap = _patch_gen_crontab(monkeypatch)
    with pytest.raises(SystemExit):
        run_gen_crontab(_base_config())
    assert "# shedule_bot" in cap.installed


def test_gen_crontab_idempotent(monkeypatch):
    existing = "# unrelated entry\n 0 10 * * *  /old/cmd --shift-type labor  # shedule_bot\n"
    cap = _patch_gen_crontab(monkeypatch, existing_crontab=existing)
    with pytest.raises(SystemExit):
        run_gen_crontab(_base_config())
    assert "# unrelated entry" in cap.installed
    assert cap.installed.count("--shift-type labor") == 1


def test_gen_crontab_fallback_prints_entries_when_install_fails(monkeypatch, capsys):
    def _fail_crontab(args, **kw):
        m = MagicMock()
        if isinstance(args, list) and args[0] == "crontab":
            raise OSError("crontab not available")
        m.stdout = "-0400\n1000\n"
        return m

    monkeypatch.setattr("main._shift_hours", lambda cfg: {"labor": "17:00"})
    monkeypatch.setattr("subprocess.run", _fail_crontab)
    with pytest.raises(SystemExit):
        run_gen_crontab(_base_config())
    out = capsys.readouterr().out
    assert "--shift-type labor" in out


def test_gen_crontab_custom_shift_type_included(monkeypatch):
    cap = _CrontabCapture()
    monkeypatch.setattr("main._shift_hours", lambda cfg: {"labor": "17:00", "night": "22:00"})
    monkeypatch.setattr("subprocess.run", cap.run)
    with pytest.raises(SystemExit):
        run_gen_crontab(_base_config())
    assert "--shift-type labor" in cap.installed
    assert "--shift-type night" in cap.installed


# --- run_verify_cron ---

def test_verify_cron_sends_to_group(monkeypatch):
    adapter_mock = MagicMock()
    monkeypatch.setattr("main.TelegramAdapter", lambda token: adapter_mock)
    monkeypatch.setattr("subprocess.run", MagicMock(return_value=MagicMock(stdout="")))
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


def test_verify_cron_self_removes_entry(monkeypatch):
    existing = (
        " 0 10 * * *  /path/main.py --production --shift-type labor  # shedule_bot\n"
        "15 10 * * *  /path/main.py --verify-cron  # shedule_bot\n"
    )

    class _Cap:
        installed = ""

        def run(self, args, **kw):
            m = MagicMock()
            m.stdout = existing if (isinstance(args, list) and "-l" in args) else ""
            if isinstance(args, list) and args[0] == "crontab" and "-l" not in args:
                _Cap.installed = kw.get("input", "")
            return m

    cap = _Cap()
    adapter_mock = MagicMock()
    monkeypatch.setattr("main.TelegramAdapter", lambda token: adapter_mock)
    monkeypatch.setattr("subprocess.run", cap.run)
    with pytest.raises(SystemExit) as exc_info:
        run_verify_cron(_base_config())
    assert exc_info.value.code == 0
    assert "--verify-cron" not in _Cap.installed
    assert "--production" in _Cap.installed
