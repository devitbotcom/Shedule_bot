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


def _col_letter_to_index(col: str) -> int:
    """Convert column letter or A1 address to 0-based index: 'C' or 'C1' → 2."""
    result = 0
    for c in col.upper():
        if c.isalpha():
            result = result * 26 + (ord(c) - ord('A') + 1)
    return result - 1


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
    rows = worksheet.get_all_values()
    if not rows:
        return []
    headers = rows[0]
    name_idx = next((i for i, h in enumerate(headers) if h == STAFF_NAME_COL), None)
    dept_idx = next((i for i, h in enumerate(headers) if h == STAFF_DEPT_COL), None)
    pref_idx = _col_letter_to_index(preferred_col) if preferred_col else None
    undes_idx = _col_letter_to_index(undesired_col) if undesired_col else None
    result = []
    for row in rows[1:]:
        name = row[name_idx].strip() if name_idx is not None and name_idx < len(row) else ""
        if not name:
            continue
        dept = row[dept_idx].strip() if dept_idx is not None and dept_idx < len(row) else ""
        pref_val = row[pref_idx].strip() if pref_idx is not None and pref_idx < len(row) else ""
        undes_val = row[undes_idx].strip() if undes_idx is not None and undes_idx < len(row) else ""
        result.append({
            "name": name,
            "department": dept,
            "preferred_days": _parse_days(pref_val),
            "undesired_days": _parse_days(undes_val),
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
