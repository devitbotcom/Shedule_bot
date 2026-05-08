import calendar
import re
from datetime import date

_NAME_RE = re.compile(r'^[\w\s\-\']+$', re.UNICODE)
_WEEKDAY_UA = {5: "субота", 6: "неділя"}


def validate_draft_grid(
    grid: list[list],
    mapping: dict,
    staff_list: list[dict],
    month_int: int,
    year_int: int,
) -> list[str]:
    """Returns list of non-blocking warning strings about Draft grid quality."""
    warnings = []

    header_idx = (mapping.get("scheduler_header_row") or mapping["header_row"]) - 1
    day_type_col = mapping.get("scheduler_day_type_column") or mapping["day_type_column"]
    dept_cols = mapping.get("scheduler_department_columns") or mapping["department_columns"]
    date_col = mapping.get("scheduler_date_column") or mapping["date_column"]

    if not grid or len(grid) <= header_idx:
        return warnings

    headers = grid[header_idx]
    col_idx = {h: i for i, h in enumerate(headers)}
    day_col_idx = col_idx.get(date_col)
    day_type_idx = col_idx.get(day_type_col)
    data_rows = grid[header_idx + 1:]

    # V1 — empty staff per department
    try:
        for dept in dept_cols:
            if not any(s.get("department") == dept for s in staff_list):
                warnings.append(f'Відділення "{dept}": немає лікарів — стовпець буде порожнім')
    except Exception:
        pass

    # V7 — staff name validation
    try:
        for s in staff_list:
            name = s.get("name", "")
            if not name or not _NAME_RE.fullmatch(name):
                warnings.append(f"Лікар: '{name}' — порожнє або містить недопустимі символи")
    except Exception:
        pass

    # Collect day numbers and per-row issues for V2, V3, V4, V5
    day_numbers: list[int] = []
    empty_day_rows = 0
    missing_day_type = 0

    for row in data_rows:
        day_val = str(row[day_col_idx]).strip() if day_col_idx is not None and day_col_idx < len(row) else ""
        day_type_val = str(row[day_type_idx]).strip() if day_type_idx is not None and day_type_idx < len(row) else ""

        if not day_val:
            empty_day_rows += 1
            continue

        try:
            day_int = int(day_val)
        except ValueError:
            continue  # non-integer cell — skip silently (AD-S006b2-003)

        day_numbers.append(day_int)
        if not day_type_val:
            missing_day_type += 1

    # V3
    if empty_day_rows:
        warnings.append(f"{empty_day_rows} рядків без номера дня")

    # V2
    if missing_day_type:
        warnings.append(
            f"{missing_day_type} днів мають номер, але тип дня не заповнено — їх буде пропущено"
        )

    # V4 — day count vs calendar
    try:
        expected = calendar.monthrange(year_int, month_int)[1]
        if len(day_numbers) != expected:
            from schedule_generator import UA_MONTHS
            month_ua = next((k for k, v in UA_MONTHS.items() if v == month_int), str(month_int))
            warnings.append(
                f"Заповнено {len(day_numbers)} днів, у {month_ua} {year_int} має бути {expected}"
            )
    except Exception:
        pass

    # V5 — days in order
    try:
        if day_numbers:
            expected_seq = list(range(day_numbers[0], day_numbers[0] + len(day_numbers)))
            if day_numbers != expected_seq:
                warnings.append("Дні йдуть не по порядку або є пропуски")
    except Exception:
        pass

    # V6 — Sat/Sun must be holiday
    try:
        for row in data_rows:
            day_val = str(row[day_col_idx]).strip() if day_col_idx is not None and day_col_idx < len(row) else ""
            day_type_val = str(row[day_type_idx]).strip() if day_type_idx is not None and day_type_idx < len(row) else ""
            if not day_val:
                continue
            try:
                day_int = int(day_val)
                d = date(year_int, month_int, day_int)
            except (ValueError, OverflowError):
                continue
            wd = d.weekday()
            if wd >= 5 and day_type_val.lower() != "holiday":
                wd_name = _WEEKDAY_UA.get(wd, "вихідний")
                warnings.append(f"День {day_int} ({wd_name}) позначено як '{day_type_val}', а не 'holiday'")
    except Exception:
        pass

    return warnings
