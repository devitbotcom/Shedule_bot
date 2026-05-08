from collections import defaultdict

UA_MONTHS = {
    "січень": 1, "лютий": 2, "березень": 3, "квітень": 4,
    "травень": 5, "червень": 6, "липень": 7, "серпень": 8,
    "вересень": 9, "жовтень": 10, "листопад": 11, "грудень": 12,
}


def generate_schedule(
    staff_list: list[dict],
    template_grid: list[list],
    mapping: dict,
) -> list[list]:
    """Returns template_grid copy with staff assigned per department using weighted greedy."""
    header_idx = (mapping.get("scheduler_header_row") or mapping["header_row"]) - 1
    day_type_col = mapping.get("scheduler_day_type_column") or mapping["day_type_column"]
    dept_cols = mapping.get("scheduler_department_columns") or mapping["department_columns"]
    date_col = mapping.get("scheduler_date_column") or mapping.get("date_column")

    if not template_grid or len(template_grid) <= header_idx:
        return [list(row) for row in template_grid]

    headers = template_grid[header_idx]
    col_idx = {h: i for i, h in enumerate(headers)}

    dept_staff: dict[str, list[dict]] = defaultdict(list)
    for s in staff_list:
        dept_staff[s["department"]].append(s)

    counts: dict[str, int] = defaultdict(int)
    result = [list(row) for row in template_grid]

    day_type_idx = col_idx.get(day_type_col)
    date_col_idx = col_idx.get(date_col) if date_col else None

    for row_idx in range(header_idx + 1, len(result)):
        row = result[row_idx]
        if day_type_idx is not None:
            day_type_val = row[day_type_idx].strip() if day_type_idx < len(row) else ""
            if not day_type_val:
                continue

        # Read day number for preference matching (C8)
        day_number = None
        if date_col_idx is not None and date_col_idx < len(row):
            try:
                day_number = int(row[date_col_idx])
            except (ValueError, TypeError):
                pass

        for dept in dept_cols:
            col = col_idx.get(dept)
            if col is None:
                continue

            # C1: skip pre-filled cells; count the pre-filled person toward balance
            current_val = row[col].strip() if col < len(row) else ""
            if current_val:
                for s in dept_staff.get(dept, []):
                    if s["name"] == current_val:
                        counts[current_val] += 1
                        break
                continue

            candidates = dept_staff.get(dept, [])
            if not candidates:
                continue

            # C8: three-tier preference selection (preferred → neutral → undesired)
            if day_number is not None:
                preferred_names = {s["name"] for s in candidates if day_number in s.get("preferred_days", [])}
                undesired_names = {s["name"] for s in candidates if day_number in s.get("undesired_days", [])}
                preferred = [s for s in candidates if s["name"] in preferred_names]
                neutral = [s for s in candidates
                           if s["name"] not in preferred_names and s["name"] not in undesired_names]
                undesired = [s for s in candidates
                             if s["name"] in undesired_names and s["name"] not in preferred_names]
            else:
                preferred, neutral, undesired = [], candidates, []

            chosen = None
            for tier in (preferred, neutral, undesired):
                if tier:
                    chosen = min(tier, key=lambda s: counts[s["name"]])
                    break

            if chosen is None:
                continue

            if col < len(row):
                row[col] = chosen["name"]
            counts[chosen["name"]] += 1

    return result
