# Sprint S006b2 — Architecture
**Date:** 2026-05-07
**Sprint:** S006b2 — Draft Validation Warnings
**Depends on:** S006b accepted

---

## Goal

When Head runs `/draft`, the bot validates the Draft tab content and appends non-blocking warnings to the confirmation message. Generation always proceeds regardless of warnings.

---

## Scope

| In | Out |
|---|---|
| Validation of Draft grid structure and content | Blocking generation on warnings |
| Non-blocking warnings in `/draft` reply + log | Validation of Staff tab structure |
| 6 checks (see below) | Per-person constraint rules (S006c) |
| New `schedule_validator.py` module | UI changes outside `/draft` |

---

## Checks

| # | Check | Condition | Warning text (Ukrainian) |
|---|---|---|---|
| V1 | Empty staff per department | `scheduler_department_columns` entry has 0 staff in Staff tab | `Відділення "<name>": немає лікарів — стовпець буде порожнім` |
| V2 | Empty day-type cells | Row has day number but day_type cell is empty | `N днів мають номер, але тип дня не заповнено — їх буде пропущено` |
| V3 | Empty day-of-month | Row after header has empty day cell | `N рядків без номера дня` |
| V4 | Day count vs calendar | Rows with day numbers ≠ `calendar.monthrange(year, month)[1]` | `Заповнено N днів, у <місяць> <рік> має бути M` |
| V5 | Days not in order | Day numbers not incrementing sequentially from 1 | `Дні йдуть не по порядку або є пропуски` |
| V6 | Sat/Sun not holiday | `date(year, month, day).weekday() >= 5` and `day_type != 'holiday'` | `День N (<weekday>) позначено як '<day_type>', а не 'holiday'` |

---

## Architecture Decisions

**AD-S006b2-001 — New module `schedule_validator.py`**
Validation logic lives in its own module, separate from `schedule_generator.py`. Single responsibility: accept inputs, return `list[str]` of warning strings. No I/O, no side effects.

Signature:
```python
def validate_draft_grid(
    grid: list[list],
    mapping: dict,
    staff_list: list[dict],
    month_int: int,
    year_int: int,
) -> list[str]:
```

**AD-S006b2-002 — Non-blocking by design**
`validate_draft_grid` never raises. All exceptions inside individual checks are caught and produce a warning rather than crashing. Generation always proceeds.

**AD-S006b2-003 — Date column key**
Day numbers are read from the column named by `scheduler_date_column` → fallback to `date_column`. Values parsed as integers; non-integer cells skipped silently. New key `scheduler_date_column` added to `schedule_mapping.json.example`.

**AD-S006b2-004 — Sat/Sun detection**
`datetime.date(year_int, month_int, day_int).weekday() >= 5` identifies Saturday (5) and Sunday (6). `day_type` compared case-insensitively to `'holiday'`. Invalid day numbers (e.g., 32) caught and skipped.

**AD-S006b2-005 — Warning format in `/draft` reply**
Warnings appended after the success line, separated by a blank line:
```
✅ Чернетку розкладу на травень 2026 записано у вкладку 'Draft-by-bot'.

⚠️ Попередження:
• Відділення "хірургія": немає лікарів — стовпець буде порожнім
• День 14 (субота) позначено як 'labour', а не 'holiday'
• Заповнено 28 днів, у травні 2026 має бути 31
```
Each warning logged at `WARNING` level before the message is sent.

**AD-S006b2-006 — Integration point in `bot_hook._cmd_draft`**
`validate_draft_grid` is called after `get_staff_list` and `get_schedule_grid`, before `generate_schedule`. Warnings collected and passed to message builder.

---

## Modified / new files

| File | Change |
|---|---|
| `schedule_validator.py` | NEW — validation logic |
| `bot_hook.py` | Call validator; append warnings to reply |
| `data/schedule_mapping.json.example` | Add `scheduler_date_column` |
| `tests/test_schedule_validator.py` | NEW — unit tests for all 6 checks |

---

## Open Questions

None — all inputs confirmed by Owner 2026-05-07.

---

## Sign-off

| Role | Date | Status |
|---|---|---|
| Architect | 2026-05-07 | ✅ |
| Developer | — | ⏸ |
| QA | — | ⏸ |
| Owner | — | ⏸ UAT pending |
