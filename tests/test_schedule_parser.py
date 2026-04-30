import os
import sys
import shutil
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from schedule_parser import parse_schedule, check_file_freshness

FIXTURE_XLSX    = os.path.join(os.path.dirname(__file__), "fixtures", "sample_schedule.xlsx")
FIXTURE_MAPPING = os.path.join(os.path.dirname(__file__), "fixtures", "schedule_mapping.json")
GROUP_CHAT_ID   = "-1001234567890"


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
    # Happy path — parser reads the fixture XLSX and returns one Shift per filled cell
    shifts = parse_schedule(stale_xlsx, GROUP_CHAT_ID, FIXTURE_MAPPING)
    # 3 rows: 1 holiday (1 dept filled) + 2 labor (2 depts each) = 5
    assert len(shifts) == 5


def test_date_stored_as_iso(stale_xlsx):
    # XLSX stores dates as DD-MM-YYYY display format — parser must convert to ISO for DB storage
    shifts = parse_schedule(stale_xlsx, GROUP_CHAT_ID, FIXTURE_MAPPING)
    for s in shifts:
        assert len(s.shift_date) == 10
        assert s.shift_date[4] == "-" and s.shift_date[7] == "-"


def test_day_type_values_valid(stale_xlsx):
    # Parser must only emit known day_type values; fixture covers both 'labor' and 'holiday'
    shifts = parse_schedule(stale_xlsx, GROUP_CHAT_ID, FIXTURE_MAPPING)
    day_types = {s.day_type for s in shifts}
    assert day_types <= {"labor", "holiday", "other"}
    assert "holiday" in day_types
    assert "labor" in day_types


def test_department_field_populated(stale_xlsx):
    # Each Shift must carry the XLSX column header as its department name
    shifts = parse_schedule(stale_xlsx, GROUP_CHAT_ID, FIXTURE_MAPPING)
    depts = {s.department for s in shifts}
    assert "Приймальне відділення" in depts
    assert "Анестезіологія" in depts


def test_employee_names_from_xlsx(stale_xlsx):
    # All four staff names in the fixture must appear — no row silently dropped
    shifts = parse_schedule(stale_xlsx, GROUP_CHAT_ID, FIXTURE_MAPPING)
    names = {s.employee_name for s in shifts}
    assert {"Alice Kovalenko", "Bob Petrenko", "Carol Melnyk", "Dan Sydorenko"} == names


def test_all_shifts_use_group_chat_id(stale_xlsx):
    # POC sends to a shared group — every Shift must target the same group chat_id
    shifts = parse_schedule(stale_xlsx, GROUP_CHAT_ID, FIXTURE_MAPPING)
    assert all(s.contact_id == GROUP_CHAT_ID for s in shifts)
    assert all(s.messenger == "telegram" for s in shifts)


def test_mtime_guard_raises_on_fresh_file(fresh_xlsx):
    # XLSX modified less than 60s ago likely means an upload is still in progress — abort
    with pytest.raises(RuntimeError, match="modified"):
        parse_schedule(fresh_xlsx, GROUP_CHAT_ID, FIXTURE_MAPPING)


def test_mtime_guard_passes_on_stale_file(stale_xlsx):
    # XLSX older than 60s is safe to read — normal cron execution path
    shifts = parse_schedule(stale_xlsx, GROUP_CHAT_ID, FIXTURE_MAPPING)
    assert len(shifts) > 0


def test_missing_required_header_exits(tmp_path, stale_xlsx):
    # IT renamed a column in XLSX — parser must exit 1 with the missing header name, not crash
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
        parse_schedule(broken, GROUP_CHAT_ID, FIXTURE_MAPPING)
    assert exc.value.code == 1


def test_urgencia_column_not_parsed(stale_xlsx):
    # Ургенція column is listed in skip_columns — it must never appear as a department
    shifts = parse_schedule(stale_xlsx, GROUP_CHAT_ID, FIXTURE_MAPPING)
    for s in shifts:
        assert s.department != "Ургенція спеціалістів на дому"


def test_missing_mapping_file_exits(stale_xlsx, tmp_path):
    # IT forgot to copy schedule_mapping.json — parser must exit 1 with a clear message
    missing = str(tmp_path / "no_such_mapping.json")
    with pytest.raises(SystemExit) as exc:
        parse_schedule(stale_xlsx, GROUP_CHAT_ID, missing)
    assert exc.value.code == 1


def test_mapping_with_custom_department_list(stale_xlsx, tmp_path):
    # IT removes a department from the mapping — parser must only emit shifts for listed depts
    import json
    mapping = {
        "header_row": 6,
        "date_column": "Дата",
        "day_type_column": "Day-type",
        "department_columns": ["Приймальне відділення"],
    }
    custom_mapping = str(tmp_path / "custom_mapping.json")
    with open(custom_mapping, "w", encoding="utf-8") as f:
        json.dump(mapping, f)
    shifts = parse_schedule(stale_xlsx, GROUP_CHAT_ID, custom_mapping)
    depts = {s.department for s in shifts}
    assert depts == {"Приймальне відділення"}


# --- Mapping dependency / precondition tests ---
# Each test mutates exactly one mapping field to a wrong value and proves
# the parser uses that field from the mapping rather than a hardcoded fallback.

def _make_mapping(tmp_path, overrides: dict) -> str:
    import json
    mapping = {
        "header_row": 6,
        "date_column": "Дата",
        "day_type_column": "Day-type",
        "department_columns": ["Приймальне відділення"],
    }
    mapping.update(overrides)
    path = str(tmp_path / "mapping.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False)
    return path


def test_precondition_header_row_read_from_mapping(stale_xlsx, tmp_path):
    # Precondition: parser must use header_row from mapping, not a hardcoded constant.
    # Wrong row → required headers not found → exit 1.
    mapping = _make_mapping(tmp_path, {"header_row": 1})
    with pytest.raises(SystemExit) as exc:
        parse_schedule(stale_xlsx, GROUP_CHAT_ID, mapping)
    assert exc.value.code == 1


def test_precondition_date_column_read_from_mapping(stale_xlsx, tmp_path):
    # Precondition: parser must use date_column from mapping, not a hardcoded constant.
    # Wrong column name → required header not found → exit 1.
    mapping = _make_mapping(tmp_path, {"date_column": "WRONG_DATE_COLUMN"})
    with pytest.raises(SystemExit) as exc:
        parse_schedule(stale_xlsx, GROUP_CHAT_ID, mapping)
    assert exc.value.code == 1


def test_precondition_day_type_column_read_from_mapping(stale_xlsx, tmp_path):
    # Precondition: parser must use day_type_column from mapping, not a hardcoded constant.
    # Wrong column name → required header not found → exit 1.
    mapping = _make_mapping(tmp_path, {"day_type_column": "WRONG_DAY_TYPE_COLUMN"})
    with pytest.raises(SystemExit) as exc:
        parse_schedule(stale_xlsx, GROUP_CHAT_ID, mapping)
    assert exc.value.code == 1
