import gspread

STAFF_NAME_COL = "Name"
STAFF_DEPT_COL = "Department"


def _parse_days(value: str) -> list[int]:
    """Parse comma-separated day numbers; skips non-integer tokens silently."""
    result = []
    for token in value.split(","):
        token = token.strip()
        if token:
            try:
                result.append(int(token))
            except ValueError:
                pass
    return result


def get_staff_list(
    sheet_id: str,
    tab_name: str,
    credentials_path: str,
    preferred_col: str | None = None,
    undesired_col: str | None = None,
) -> list[dict]:
    """Returns list of {name, department, preferred_days, undesired_days} dicts from the staff tab."""
    gc = gspread.service_account(filename=credentials_path)
    worksheet = gc.open_by_key(sheet_id).worksheet(tab_name)
    records = worksheet.get_all_records()
    result = []
    for row in records:
        if not row.get(STAFF_NAME_COL):
            continue
        result.append({
            "name": str(row[STAFF_NAME_COL]).strip(),
            "department": str(row[STAFF_DEPT_COL]).strip(),
            "preferred_days": _parse_days(str(row.get(preferred_col) or "")) if preferred_col else [],
            "undesired_days": _parse_days(str(row.get(undesired_col) or "")) if undesired_col else [],
        })
    return result


def get_schedule_grid(sheet_id: str, tab_name: str, credentials_path: str) -> list[list]:
    """Returns all cell values as a 2D list — same raw shape as openpyxl iter_rows."""
    gc = gspread.service_account(filename=credentials_path)
    worksheet = gc.open_by_key(sheet_id).worksheet(tab_name)
    return worksheet.get_all_values()


def read_cell(sheet_id: str, tab_name: str, cell: str, credentials_path: str) -> str:
    """Returns the string value of a single cell (e.g. 'A1')."""
    gc = gspread.service_account(filename=credentials_path)
    worksheet = gc.open_by_key(sheet_id).worksheet(tab_name)
    return str(worksheet.acell(cell).value or "")


def write_schedule_grid(sheet_id: str, tab_name: str, rows: list[list], credentials_path: str) -> None:
    """Writes rows to tab_name. Creates tab if absent; clears and overwrites if present."""
    gc = gspread.service_account(filename=credentials_path)
    spreadsheet = gc.open_by_key(sheet_id)
    try:
        worksheet = spreadsheet.worksheet(tab_name)
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=max(len(rows) + 10, 50), cols=50)
    if rows:
        worksheet.update(rows)
