import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config as config_module


def _set_env(monkeypatch, overrides: dict):
    defaults = {
        "XLSX_PATH": "/tmp/schedule.xlsx",
        "DB_PATH": "/tmp/shift_bot.db",
        "LOG_DIR": "/tmp/logs",
        "CONTACTS_PATH": "/tmp/contacts.json",
        "TELEGRAM_BOT_TOKEN": "test-token",
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        if v is None:
            monkeypatch.delenv(k, raising=False)
        else:
            monkeypatch.setenv(k, v)


def test_all_vars_present(monkeypatch):
    _set_env(monkeypatch, {})
    cfg = config_module.load_config()
    assert cfg["XLSX_PATH"] == "/tmp/schedule.xlsx"
    assert cfg["CONTACTS_PATH"] == "/tmp/contacts.json"


def test_missing_one_var(monkeypatch, capsys):
    _set_env(monkeypatch, {"TELEGRAM_BOT_TOKEN": None})
    with pytest.raises(SystemExit) as exc:
        config_module.load_config()
    assert exc.value.code == 1
    assert "TELEGRAM_BOT_TOKEN" in capsys.readouterr().out


def test_missing_multiple_vars(monkeypatch, capsys):
    _set_env(monkeypatch, {"DB_PATH": None, "LOG_DIR": None})
    with pytest.raises(SystemExit) as exc:
        config_module.load_config()
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "DB_PATH" in out
    assert "LOG_DIR" in out
