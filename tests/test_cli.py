import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cli import parse_args


def _parse(args: list):
    sys.argv = ["main.py"] + args
    return parse_args()


def test_no_flags_is_health():
    # IT runs `python main.py` with no flags → health check mode, nothing sent
    mode = _parse([])
    assert mode.mode == "health"
    assert mode.employee is None
    assert mode.force is False
    assert mode.dry_run is False


def test_production():
    # IT runs `python main.py --production` → sends real notifications
    mode = _parse(["--production"])
    assert mode.mode == "production"


def test_dry_run():
    # IT runs `python main.py --dry-run` before go-live → previews shifts, nothing sent
    mode = _parse(["--dry-run"])
    assert mode.mode == "dry_run"
    assert mode.dry_run is True


def test_production_employee():
    # IT resends a missed notification to one person without triggering the whole staff
    mode = _parse(["--production", "--employee", "Alice Kovalenko"])
    assert mode.mode == "production"
    assert mode.employee == "Alice Kovalenko"


def test_production_force():
    # IT force-resends all notifications ignoring deduplication (e.g. after a data fix)
    mode = _parse(["--production", "--force"])
    assert mode.mode == "production"
    assert mode.force is True


def test_reload_schedule():
    # IT uploads a corrected XLSX and clears dedup records so cron will re-send
    mode = _parse(["--reload-schedule"])
    assert mode.mode == "reload_schedule"


def test_reload_schedule_dry_run():
    # IT previews which dedup records would be cleared before committing to reload
    mode = _parse(["--reload-schedule", "--dry-run"])
    assert mode.mode == "reload_schedule"
    assert mode.dry_run is True


def test_force_without_production_exits(capsys):
    # Accidental `--force` without `--production` is rejected — no silent no-op
    with pytest.raises(SystemExit) as exc:
        _parse(["--force"])
    assert exc.value.code == 2


def test_employee_without_production_exits(capsys):
    # `--employee` without `--production` is rejected — name filter requires real send mode
    with pytest.raises(SystemExit) as exc:
        _parse(["--employee", "Alice"])
    assert exc.value.code == 2


def test_dry_run_with_production_exits(capsys):
    # `--dry-run` and `--production` together are rejected — mutually exclusive intents
    with pytest.raises(SystemExit) as exc:
        _parse(["--production", "--dry-run"])
    assert exc.value.code == 2


def test_production_date():
    # IT reruns a missed send for a past date without changing today's cron run
    mode = _parse(["--production", "--date", "2026-04-28"])
    assert mode.mode == "production"
    assert mode.date == "2026-04-28"


def test_date_without_production_exits(capsys):
    # `--date` without `--production` is rejected — date override only makes sense for real sends
    with pytest.raises(SystemExit) as exc:
        _parse(["--date", "2026-04-28"])
    assert exc.value.code == 2


def test_date_invalid_format_exits(capsys):
    # `--date` with wrong format is rejected immediately rather than failing at runtime
    with pytest.raises(SystemExit) as exc:
        _parse(["--production", "--date", "28-04-2026"])
    assert exc.value.code == 2


def test_shift_type():
    # gen_crontab passes --shift-type so each cron entry sends only its day_type
    mode = _parse(["--production", "--shift-type", "labour"])
    assert mode.mode == "production"
    assert mode.shift_type == "labour"


def test_shift_type_without_production_exits(capsys):
    # --shift-type without --production is rejected — filter only applies to real sends
    with pytest.raises(SystemExit) as exc:
        _parse(["--shift-type", "labour"])
    assert exc.value.code == 2
