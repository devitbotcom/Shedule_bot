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
    header_idx = mapping["header_row"] - 1
    day_type_col = mapping["day_type_column"]
    dept_cols = mapping["department_columns"]

    if not template_grid or len(template_grid) <= header_idx:
        return [list(row) for row in template_grid]

    headers = template_grid[header_idx]
    col_idx = {h: i for i, h in enumerate(headers)}

    dept_staff: dict[str, list[str]] = defaultdict(list)
    for s in staff_list:
        dept_staff[s["department"]].append(s["name"])

    counts: dict[str, int] = defaultdict(int)
    result = [list(row) for row in template_grid]

    day_type_idx = col_idx.get(day_type_col)

    for row_idx in range(header_idx + 1, len(result)):
        row = result[row_idx]
        if day_type_idx is not None:
            day_type_val = row[day_type_idx].strip() if day_type_idx < len(row) else ""
            if not day_type_val:
                continue
        for dept in dept_cols:
            col = col_idx.get(dept)
            if col is None:
                continue
            candidates = dept_staff.get(dept, [])
            if not candidates:
                continue
            chosen = min(candidates, key=lambda n: counts[n])
            if col < len(row):
                row[col] = chosen
            counts[chosen] += 1

    return result
