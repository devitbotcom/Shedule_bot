import calendar
import re
from datetime import date

_NAME_RE = re.compile(r'^(?!.*\.{2})[\w\s\-\'\.]+$', re.UNICODE)
_WEEKDAY_UA = {
    0: "понеділок", 1: "вівторок", 2: "середа",
    3: "четвер", 4: "п'ятниця", 5: "субота", 6: "неділя",
}


def _cell(row: list, idx) -> str:
    """Safe cell read: returns empty string for missing index or None value."""
    if idx is None or idx >= len(row):
        return ""
    val = row[idx]
    return str(val).strip() if val is not None else ""


def validate_draft_grid(
    grid: list[list],
    mapping: dict,
    staff_list: list[dict],
    month_int: int,
    year_int: int | None,
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

    # Column-not-found diagnostics — emitted before any data checks
    if day_col_idx is None:
        warnings.append(
            f"[Налаштування] стовпець '{date_col}' не знайдено в заголовку — перевірте scheduler_date_column"
        )
    if day_type_idx is None:
        warnings.append(
            f"[Налаштування] стовпець типу дня '{day_type_col}' не знайдено — перевірте scheduler_day_type_column"
        )

    # V1 — empty staff per department
    try:
        for dept in dept_cols:
            if not any(s.get("department") == dept for s in staff_list):
                warnings.append(f"[Персонал] відділення '{dept}' — немає лікарів, стовпець буде порожнім")
    except Exception:
        pass

    # V7 — staff name validation
    try:
        for s in staff_list:
            name = s.get("name", "")
            if not name:
                warnings.append(f"[Персонал] лікар '' — порожнє ім'я")
            elif not _NAME_RE.fullmatch(name):
                warnings.append(f"[Персонал] лікар '{name}' — недопустимі символи в імені")
    except Exception:
        pass

    # Collect day numbers and per-row issues for V2, V3, V4, V5
    # C4: skip entire loop when date column is missing to prevent V3 cascade noise
    day_numbers: list[int] = []
    empty_day_rows = 0
    missing_day_type_days: list[int] = []

    if day_col_idx is not None:
        for row in data_rows:
            day_val = _cell(row, day_col_idx)
            day_type_val = _cell(row, day_type_idx)

            if not day_val:
                empty_day_rows += 1
                continue

            try:
                day_int = int(day_val)
            except ValueError:
                continue  # non-integer cell — skip silently (AD-S006b2-003)

            day_numbers.append(day_int)
            if not day_type_val:
                missing_day_type_days.append(day_int)

    # V3
    if empty_day_rows:
        warnings.append(f"[Структура] {empty_day_rows} рядків без номера дня")

    # V2
    if missing_day_type_days:
        days_str = ", ".join(str(d) for d in missing_day_type_days)
        warnings.append(f"[Структура] тип дня не заповнено: дні {days_str}")

    # V4 — day count vs calendar (requires year_int)
    if year_int is not None:
        try:
            expected = calendar.monthrange(year_int, month_int)[1]
            if len(day_numbers) != expected:
                from schedule_generator import UA_MONTHS
                month_ua = next((k for k, v in UA_MONTHS.items() if v == month_int), str(month_int))
                warnings.append(
                    f"[Структура] заповнено {len(day_numbers)} днів, очікується {expected} ({month_ua} {year_int})"
                )
        except Exception:
            pass

    # V5 — days in order (show first out-of-order position)
    try:
        if day_numbers:
            expected_seq = list(range(day_numbers[0], day_numbers[0] + len(day_numbers)))
            if day_numbers != expected_seq:
                for pos, (actual, exp) in enumerate(zip(day_numbers, expected_seq), start=1):
                    if actual != exp:
                        prev = day_numbers[pos - 2]
                        warnings.append(
                            f"[День {actual}] порядок порушено — після дня {prev} очікувався день {exp}"
                        )
                        break
    except Exception:
        pass

    # V6/V6b — weekend/weekday day-type mismatch (requires year_int)
    if year_int is not None:
        try:
            for row in data_rows:
                day_val = _cell(row, day_col_idx)
                day_type_val = _cell(row, day_type_idx)
                if not day_val:
                    continue
                try:
                    day_int = int(day_val)
                    d = date(year_int, month_int, day_int)
                except (ValueError, OverflowError, TypeError):
                    continue
                wd = d.weekday()
                wd_name = _WEEKDAY_UA.get(wd, "вихідний")
                if wd >= 5 and day_type_val.lower() != "holiday":
                    warnings.append(
                        f"[День {day_int}] {wd_name} — тип '{day_type_val}', очікується 'holiday'"
                    )
                elif wd < 5 and day_type_val.lower() == "holiday":
                    warnings.append(
                        f"[День {day_int}] {wd_name} — тип 'holiday', очікується 'labour'"
                    )
        except Exception:
            pass

    return warnings
