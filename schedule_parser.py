import logging
import os
import sys
import time
from datetime import datetime

import openpyxl

from models import Shift

logger = logging.getLogger(__name__)

COL_SHIFT_DATE    = "shift_date"
COL_EMPLOYEE_NAME = "employee_name"
COL_DUTY_TYPE     = "duty_type"
COL_ROLE          = "role"
COL_MESSENGER     = "messenger"
COL_CONTACT_ID    = "contact_id"

SHEET_SCHEDULE  = 1   # Sheet index (1-based in openpyxl active/sheet access)
SHEET_REGISTRY  = 2


def check_file_freshness(xlsx_path: str, threshold_seconds: int = 60) -> None:
    mtime = os.path.getmtime(xlsx_path)
    age = time.time() - mtime
    if age < threshold_seconds:
        modified_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        raise RuntimeError(
            f"XLSX was modified {age:.0f}s ago (at {modified_at}) — "
            f"possible upload in progress. Skipping run. Path: {xlsx_path}"
        )


def _get_headers(sheet) -> dict:
    headers = {}
    for col_idx, cell in enumerate(next(sheet.iter_rows(min_row=1, max_row=1)), start=1):
        if cell.value:
            headers[str(cell.value).strip().lower()] = col_idx
    return headers


def _require_columns(headers: dict, required: list, sheet_name: str) -> None:
    for col in required:
        if col not in headers:
            logger.error("Missing column '%s' in sheet '%s'", col, sheet_name)
            print(f"[XLSX]    ❌ missing column '{col}' in sheet '{sheet_name}'")
            sys.exit(1)


def parse_schedule(xlsx_path: str, location_default: str) -> list:
    check_file_freshness(xlsx_path)

    try:
        wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    except Exception as exc:
        logger.error("Cannot open XLSX: %s — %s", xlsx_path, exc)
        print(f"[XLSX]    ❌ cannot open file: {xlsx_path}")
        sys.exit(1)

    sheet_names = wb.sheetnames
    if len(sheet_names) < 2:
        logger.error("XLSX must have at least 2 sheets; found %d", len(sheet_names))
        print("[XLSX]    ❌ expected 2 sheets (Schedule, Employee Registry)")
        sys.exit(1)

    # --- Sheet 1: Schedule ---
    ws_schedule = wb.worksheets[0]
    sched_headers = _get_headers(ws_schedule)
    _require_columns(sched_headers, [COL_SHIFT_DATE, COL_EMPLOYEE_NAME, COL_DUTY_TYPE], sheet_names[0])

    # --- Sheet 2: Employee Registry ---
    ws_registry = wb.worksheets[1]
    reg_headers = _get_headers(ws_registry)
    _require_columns(reg_headers, [COL_EMPLOYEE_NAME, COL_ROLE, COL_MESSENGER, COL_CONTACT_ID], sheet_names[1])

    registry = {}
    for row in ws_registry.iter_rows(min_row=2, values_only=True):
        name = row[reg_headers[COL_EMPLOYEE_NAME] - 1]
        if not name:
            continue
        name = str(name).strip()
        registry[name] = {
            COL_ROLE:       str(row[reg_headers[COL_ROLE] - 1] or "").strip(),
            COL_MESSENGER:  str(row[reg_headers[COL_MESSENGER] - 1] or "").strip().lower(),
            COL_CONTACT_ID: str(row[reg_headers[COL_CONTACT_ID] - 1] or "").strip(),
        }

    shifts = []
    for row in ws_schedule.iter_rows(min_row=2, values_only=True):
        raw_date     = row[sched_headers[COL_SHIFT_DATE] - 1]
        employee_name = str(row[sched_headers[COL_EMPLOYEE_NAME] - 1] or "").strip()
        duty_type    = str(row[sched_headers[COL_DUTY_TYPE] - 1] or "").strip()

        if not employee_name or not raw_date:
            continue

        # Convert date: accept DD-MM-YYYY string or datetime object
        if isinstance(raw_date, datetime):
            shift_date = raw_date.strftime("%Y-%m-%d")
        else:
            try:
                shift_date = datetime.strptime(str(raw_date).strip(), "%d-%m-%Y").strftime("%Y-%m-%d")
            except ValueError:
                logger.warning("Unrecognised date format '%s' for employee '%s' — skipping", raw_date, employee_name)
                continue

        if employee_name not in registry:
            logger.warning("Employee '%s' not in registry — skipping", employee_name)
            continue

        emp = registry[employee_name]
        if not emp[COL_CONTACT_ID]:
            logger.warning("Empty contact_id for employee '%s' — skipping", employee_name)
            continue

        shifts.append(Shift(
            employee_name=employee_name,
            role=emp[COL_ROLE],
            duty_type=duty_type,
            shift_date=shift_date,
            location=location_default,
            messenger=emp[COL_MESSENGER],
            contact_id=emp[COL_CONTACT_ID],
        ))

    return shifts
