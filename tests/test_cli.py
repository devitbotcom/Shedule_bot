import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cli import parse_args


def _parse(args: list):
    sys.argv = ["main.py"] + args
    return parse_args()


def test_no_flags_is_health():
    mode = _parse([])
    assert mode.mode == "health"
    assert mode.employee is None
    assert mode.force is False
    assert mode.dry_run is False


def test_production():
    mode = _parse(["--production"])
    assert mode.mode == "production"


def test_dry_run():
    mode = _parse(["--dry-run"])
    assert mode.mode == "dry_run"
    assert mode.dry_run is True


def test_production_employee():
    mode = _parse(["--production", "--employee", "Alice Kovalenko"])
    assert mode.mode == "production"
    assert mode.employee == "Alice Kovalenko"


def test_production_force():
    mode = _parse(["--production", "--force"])
    assert mode.mode == "production"
    assert mode.force is True


def test_reload_schedule():
    mode = _parse(["--reload-schedule"])
    assert mode.mode == "reload_schedule"


def test_reload_schedule_dry_run():
    mode = _parse(["--reload-schedule", "--dry-run"])
    assert mode.mode == "reload_schedule"
    assert mode.dry_run is True


def test_force_without_production_exits(capsys):
    with pytest.raises(SystemExit) as exc:
        _parse(["--force"])
    assert exc.value.code == 2


def test_employee_without_production_exits(capsys):
    with pytest.raises(SystemExit) as exc:
        _parse(["--employee", "Alice"])
    assert exc.value.code == 2


def test_dry_run_with_production_exits(capsys):
    with pytest.raises(SystemExit) as exc:
        _parse(["--production", "--dry-run"])
    assert exc.value.code == 2
