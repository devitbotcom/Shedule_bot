import gspread

STAFF_NAME_COL = "Name"
STAFF_DEPT_COL = "Department"


def get_staff_list(sheet_id: str, tab_name: str, credentials_path: str) -> list[dict]:
    """Returns list of {name, department} dicts from the staff tab."""
    gc = gspread.service_account(filename=credentials_path)
    worksheet = gc.open_by_key(sheet_id).worksheet(tab_name)
    records = worksheet.get_all_records()
    return [
        {"name": row[STAFF_NAME_COL], "department": row[STAFF_DEPT_COL]}
        for row in records
        if row.get(STAFF_NAME_COL)
    ]


def get_schedule_grid(sheet_id: str, tab_name: str, credentials_path: str) -> list[list]:
    """Returns all cell values as a 2D list — same raw shape as openpyxl iter_rows."""
    gc = gspread.service_account(filename=credentials_path)
    worksheet = gc.open_by_key(sheet_id).worksheet(tab_name)
    return worksheet.get_all_values()
