import json
import logging
import os
import sys
import time
from datetime import datetime

import openpyxl

from models import Shift

logger = logging.getLogger(__name__)

VALID_DAY_TYPES = {"labor", "holiday", "other"}
_DAY_TYPE_ALIASES = {"labour": "labor"}  # normalize British spelling from XLSX


def check_file_freshness(xlsx_path: str, threshold_seconds: int = 60) -> None:
    mtime = os.path.getmtime(xlsx_path)
    age = time.time() - mtime
    if age < threshold_seconds:
        modified_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        raise RuntimeError(
            f"XLSX was modified {age:.0f}s ago (at {modified_at}) — "
            f"possible upload in progress. Path: {xlsx_path}"
        )


def load_mapping(mapping_path: str) -> dict:
    if not os.path.exists(mapping_path):
        print(f"[MAPPING] ❌ schedule_mapping.json not found: {mapping_path}")
        print(f"          Copy data/schedule_mapping.json.example → data/schedule_mapping.json and update column names.")
        sys.exit(1)
    try:
        with open(mapping_path, encoding="utf-8") as f:
            m = json.load(f)
    except Exception as exc:
        print(f"[MAPPING] ❌ cannot parse schedule_mapping.json: {exc}")
        sys.exit(1)

    required_keys = {"header_row", "date_column", "day_type_column", "department_columns"}
    missing = required_keys - m.keys()
    if missing:
        print(f"[MAPPING] ❌ schedule_mapping.json missing keys: {', '.join(sorted(missing))}")
        sys.exit(1)

    import re
    for day_type, time_val in m.get("shift_hours", {}).items():
        if not re.match(r"^\d{2}:\d{2}$", str(time_val)):
            print(f"[MAPPING] ❌ shift_hours.{day_type}: invalid time format '{time_val}' — expected HH:MM")
            sys.exit(1)

    return m


def _build_header_map(sheet, header_row: int) -> dict[str, int]:
    rows = list(sheet.iter_rows(min_row=header_row, max_row=header_row, values_only=True))
    header_map: dict[str, int] = {}
    for col_idx, value in enumerate(rows[0], start=1):
        if value is not None:
            header_map[str(value).strip()] = col_idx
    return header_map


def _require_headers(header_map: dict[str, int], required: list[str]) -> None:
    missing = [h for h in required if h not in header_map]
    if not missing:
        return
    for h in missing:
        logger.critical("Missing required XLSX header: '%s'", h)
        print(f"[XLSX]    ❌ missing required header: '{h}'")
    sys.exit(1)


def _parse_date(raw: object, context: str) -> str | None:
    if isinstance(raw, datetime):
        return raw.strftime("%Y-%m-%d")
    try:
        return datetime.strptime(str(raw).strip(), "%d-%m-%Y").strftime("%Y-%m-%d")
    except ValueError:
        logger.warning("Unrecognised date '%s' on row %s — skipping", raw, context)
        return None


def parse_schedule(xlsx_path: str, group_chat_id: str, mapping_path: str) -> list[Shift]:
    check_file_freshness(xlsx_path)
    mapping = load_mapping(mapping_path)

    header_row    = mapping["header_row"]
    hdr_date      = mapping["date_column"]
    hdr_day_type  = mapping["day_type_column"]
    dept_headers  = mapping["department_columns"]
    skip_headers  = mapping.get("skip_columns", [])

    required_headers = [hdr_date, hdr_day_type] + dept_headers

    try:
        wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    except Exception as exc:
        logger.critical("Cannot open XLSX: %s — %s", xlsx_path, exc)
        print(f"[XLSX]    ❌ cannot open: {xlsx_path}")
        sys.exit(1)

    ws = wb.worksheets[0]
    header_map = _build_header_map(ws, header_row)
    _require_headers(header_map, required_headers)

    for hdr in skip_headers:
        if hdr in header_map:
            logger.info("Column '%s' found but skipped (listed in skip_columns)", hdr)

    shifts: list[Shift] = []

    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        raw_date     = row[header_map[hdr_date] - 1]
        raw_day_type = row[header_map[hdr_day_type] - 1]

        if raw_date is None:
            continue

        shift_date = _parse_date(raw_date, str(raw_date))
        if shift_date is None:
            continue

        day_type = str(raw_day_type or "").strip().lower()
        day_type = _DAY_TYPE_ALIASES.get(day_type, day_type)
        if day_type not in VALID_DAY_TYPES:
            logger.warning("Unknown day_type '%s' on %s — skipping row", day_type, shift_date)
            continue

        for dept in dept_headers:
            if dept not in header_map:
                continue
            cell_value = row[header_map[dept] - 1]
            if cell_value is None:
                continue

            employee_name = str(cell_value).strip()
            if not employee_name:
                continue

            shifts.append(Shift(
                employee_name=employee_name,
                department=dept,
                day_type=day_type,
                shift_date=shift_date,
                messenger="telegram",
                contact_id=group_chat_id,
            ))

    return shifts
