import json
import os
import subprocess
import sys
import tempfile
import pathlib
import pytest

_ROOT = pathlib.Path(__file__).parent.parent
_SCRIPT = _ROOT / "gen_crontab.py"
_OUTPUT = _ROOT / "crontab.generated"


def _run(shift_hours: dict) -> tuple[int, str]:
    """Run gen_crontab.py with a temp mapping file; return (returncode, crontab text)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mapping = {"shift_hours": shift_hours}
        (pathlib.Path(tmpdir) / "schedule_mapping.json").write_text(
            json.dumps(mapping), encoding="utf-8"
        )
        fake_xlsx = pathlib.Path(tmpdir) / "schedule.xlsx"
        fake_xlsx.touch()

        env = os.environ.copy()
        env["XLSX_PATH"] = str(fake_xlsx)

        result = subprocess.run(
            [sys.executable, str(_SCRIPT)],
            env=env,
            capture_output=True,
            text=True,
        )
        content = _OUTPUT.read_text(encoding="utf-8") if _OUTPUT.exists() else ""
        return result.returncode, content


@pytest.fixture(autouse=True)
def cleanup():
    yield
    _OUTPUT.unlink(missing_ok=True)


def _cron_lines(shift_hours: dict) -> list[str]:
    rc, text = _run(shift_hours)
    assert rc == 0, f"gen_crontab.py exited {rc}"
    return [l for l in text.splitlines() if l and not l.startswith("#")]


def test_single_shift_type():
    lines = _cron_lines({"labour": "17:00"})
    assert len(lines) == 1
    assert lines[0] == "0 17 * * * python /app/main.py --production --shift-type labour"


def test_multiple_shift_types():
    lines = _cron_lines({"holiday": "09:00", "labour": "17:00"})
    assert len(lines) == 2
    assert any("--shift-type holiday" in l and "0 9" in l for l in lines)
    assert any("--shift-type labour" in l and "0 17" in l for l in lines)


def test_same_time_produces_separate_entries():
    # holiday and other share 09:00 — each still gets its own cron line
    lines = _cron_lines({"holiday": "09:00", "other": "09:00"})
    assert len(lines) == 2
    assert any("--shift-type holiday" in l for l in lines)
    assert any("--shift-type other" in l for l in lines)


def test_new_day_type_from_config():
    # IT adds a new shift type — no code change needed
    lines = _cron_lines({"night": "23:00"})
    assert len(lines) == 1
    assert lines[0] == "0 23 * * * python /app/main.py --production --shift-type night"


def test_minute_parsed_correctly():
    lines = _cron_lines({"labour": "22:50"})
    assert lines[0].startswith("50 22")


def test_missing_mapping_exits_nonzero():
    env = os.environ.copy()
    env["XLSX_PATH"] = "/nonexistent/schedule.xlsx"
    result = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "not found" in result.stderr
