import json
import os
import sys
import shutil
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from schedule_parser import parse_schedule, check_file_freshness

FIXTURE_XLSX     = os.path.join(os.path.dirname(__file__), "fixtures", "sample_schedule.xlsx")
FIXTURE_CONTACTS = os.path.join(os.path.dirname(__file__), "fixtures", "contacts.json")


@pytest.fixture
def stale_xlsx(tmp_path):
    dest = tmp_path / "schedule.xlsx"
    shutil.copy(FIXTURE_XLSX, dest)
    os.utime(dest, (time.time() - 90, time.time() - 90))
    return str(dest)


@pytest.fixture
def fresh_xlsx(tmp_path):
    dest = tmp_path / "schedule.xlsx"
    shutil.copy(FIXTURE_XLSX, dest)
    return str(dest)


def test_valid_xlsx_returns_five_shifts(stale_xlsx):
    shifts = parse_schedule(stale_xlsx, FIXTURE_CONTACTS)
    # 3 rows: 1 holiday (1 dept filled) + 2 labor (2 depts each) = 5
    assert len(shifts) == 5


def test_date_stored_as_iso(stale_xlsx):
    shifts = parse_schedule(stale_xlsx, FIXTURE_CONTACTS)
    for s in shifts:
        assert len(s.shift_date) == 10
        assert s.shift_date[4] == "-" and s.shift_date[7] == "-"


def test_day_type_values_valid(stale_xlsx):
    shifts = parse_schedule(stale_xlsx, FIXTURE_CONTACTS)
    day_types = {s.day_type for s in shifts}
    assert day_types <= {"labor", "holiday", "other"}
    assert "holiday" in day_types
    assert "labor" in day_types


def test_department_field_populated(stale_xlsx):
    shifts = parse_schedule(stale_xlsx, FIXTURE_CONTACTS)
    depts = {s.department for s in shifts}
    assert "Приймальне відділення" in depts
    assert "Анестезіологія" in depts


def test_employee_names_match_fixture(stale_xlsx):
    shifts = parse_schedule(stale_xlsx, FIXTURE_CONTACTS)
    names = {s.employee_name for s in shifts}
    assert {"Alice Kovalenko", "Bob Petrenko", "Carol Melnyk", "Dan Sydorenko"} == names


def test_mtime_guard_raises_on_fresh_file(fresh_xlsx):
    with pytest.raises(RuntimeError, match="modified"):
        parse_schedule(fresh_xlsx, FIXTURE_CONTACTS)


def test_mtime_guard_passes_on_stale_file(stale_xlsx):
    shifts = parse_schedule(stale_xlsx, FIXTURE_CONTACTS)
    assert len(shifts) > 0


def test_missing_required_header_exits(tmp_path, stale_xlsx):
    import openpyxl
    wb = openpyxl.load_workbook(stale_xlsx)
    ws = wb.worksheets[0]
    for cell in ws[6]:
        if cell.value == "Day-type":
            cell.value = "REMOVED"
    broken = str(tmp_path / "broken.xlsx")
    wb.save(broken)
    os.utime(broken, (time.time() - 90, time.time() - 90))
    with pytest.raises(SystemExit) as exc:
        parse_schedule(broken, FIXTURE_CONTACTS)
    assert exc.value.code == 1


def test_unknown_employee_skipped(stale_xlsx, tmp_path):
    partial = [{"name": "Alice Kovalenko", "channels": {"telegram": "111"}, "primary_channel": "telegram"}]
    contacts_path = str(tmp_path / "contacts.json")
    with open(contacts_path, "w") as f:
        json.dump(partial, f)
    shifts = parse_schedule(stale_xlsx, contacts_path)
    names = {s.employee_name for s in shifts}
    assert "Alice Kovalenko" in names
    assert "Bob Petrenko" not in names


def test_urgencia_column_not_parsed(stale_xlsx):
    shifts = parse_schedule(stale_xlsx, FIXTURE_CONTACTS)
    for s in shifts:
        assert s.department != "Ургенція спеціалістів на дому"
