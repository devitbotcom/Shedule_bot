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
| Non-blocking warnings in `/draft` reply + log | Validation of Staff tab columns/schema |
| 7 checks (see below) | Per-person constraint rules (S006c) |
| Trim whitespace from staff names at read time | UI changes outside `/draft` |
| Staff name alphanumeric validation | — |
| New `schedule_validator.py` module | — |

---

## Checks

**Updated 2026-05-08 — unified message format (see AD-S006b2-008)**

| # | Check | Condition | Warning text (Ukrainian) |
|---|---|---|---|
| col | Column not found (date) | `date_col` absent from header row | `[Налаштування] стовпець 'X' не знайдено в заголовку — перевірте scheduler_date_column` |
| col | Column not found (day-type) | `day_type_col` absent from header row | `[Налаштування] стовпець типу дня 'X' не знайдено — перевірте scheduler_day_type_column` |
| V1 | Empty staff per department | `scheduler_department_columns` entry has 0 staff in Staff tab | `[Персонал] відділення 'X' — немає лікарів, стовпець буде порожнім` |
| V2 | Empty day-type cells | Row has day number but day_type cell is empty | `[Структура] тип дня не заповнено: дні 5, 12, 20` (aggregated list of day numbers) |
| V3 | Empty day-of-month | Row after header has empty day cell | `[Структура] N рядків без номера дня` |
| V4 | Day count vs calendar | Rows with day numbers ≠ `calendar.monthrange(year, month)[1]` | `[Структура] заповнено N днів, очікується M (місяць рік)` |
| V5 | Days not in order | Day numbers not incrementing sequentially | `[День {actual}] порядок порушено — після дня {prev} очікувався день {exp}` |
| V6 | Sat/Sun not holiday | `weekday() >= 5` and `day_type != 'holiday'` | `[День N] субота/неділя — тип 'X', очікується 'holiday'` |
| V6b | Mon–Fri marked holiday | `weekday() < 5` and `day_type == 'holiday'` | `[День N] вівторок/etc — тип 'holiday', очікується 'labour'` |
| V7 | Staff name empty | Name empty after trim | `[Персонал] лікар '' — порожнє ім'я` |
| V7 | Staff name invalid chars | Name does not match `[\w\s\-\']+` (Unicode) | `[Персонал] лікар 'X' — недопустимі символи в імені` |

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

**AD-S006b2-007 — Trim at the adapter boundary**
`get_staff_list` in `google_sheets_adapter.py` strips leading/trailing whitespace from `name` and `department` values on read. Silent — no warning. Ensures all downstream code (generator, validator) receives clean strings. V7 then checks the already-trimmed names for emptiness or invalid characters.

**AD-S006b2-006 — Integration point in `bot_hook._cmd_draft`**
`validate_draft_grid` is called after `get_staff_list` and `get_schedule_grid`, before `generate_schedule`. Warnings collected and passed to message builder.

**AD-S006b2-008 — Unified warning message format (2026-05-08)**
All warning strings use the prefix pattern `[Категорія] message`.

Four categories:
- `[Налаштування]` — column mapping config problems
- `[Персонал]` — Staff tab data problems (V1, V7)
- `[Структура]` — grid shape/count problems (V3, V4) and aggregated data issues (V2)
- `[День N]` — per-day data problems, N is the day number visible in the spreadsheet (V5, V6, V6b)

`[День N]` tags are the primary navigation aid: the Head can locate the row in the Draft tab by the day number in the Day column.

V2 changes from a counter to an aggregated list: `[Структура] тип дня не заповнено: дні 5, 12, 20`. Implementation: change `missing_day_type` counter to `missing_day_type_days: list[int]`, append `day_int` instead of incrementing, format with `", ".join(...)`.

V7 splits the combined "порожнє або недопустимі символи" into two distinct messages to keep each warning actionable.

No logic changes to any check — format only.

---

## Test plan — `tests/test_schedule_validator.py`

**Base fixture** — June 2026 (June 1 = Monday, June 6 = Saturday; 30 days):

```python
_MAPPING = {
    "scheduler_header_row": 1,
    "scheduler_date_column": "Day",
    "scheduler_day_type_column": "Day-type",
    "scheduler_department_columns": ["Surgery"],
    "date_column": "Day",
    "day_type_column": "Day-type",
    "department_columns": ["Surgery"],
}
_STAFF = [{"name": "Alice", "department": "Surgery"}]
_MONTH, _YEAR = 6, 2026
```

**Test table — 13 tests:**

| # | Test | Input variation | Check | Technique | Expected |
|---|---|---|---|---|---|
| 1 | No warnings — valid grid | header + days 1,2 (`labour`), staff present | all | EP (valid) | `[]` |
| 2 | Empty staff for department | `staff_list = []` | V1 | Negative | warning contains `"Surgery"` |
| 3 | Day number present, day-type empty | row `["5", "", ""]` | V2 | Negative | warning contains count + `"пропущено"` |
| 4 | Empty day cell | row `["", "labour", ""]` | V3 | Negative | warning contains `"рядків без номера"` |
| 5a | Leap year Feb — 29 rows valid | days 1–29, month=Feb, year=2028 | V4 | Boundary (leap) | no V4 warning |
| 5b | Non-leap Feb — 29 rows invalid | days 1–29, month=Feb, year=2029 | V4 | Boundary (non-leap) | warning contains `"29"` and `"28"` |
| 6 | Days out of order | days `[1, 3, 2]` | V5 | Negative | warning contains `"порядку"` |
| 7 | Saturday marked `labour` | day 6 (Sat in June 2026), day_type=`labour` | V6 | Negative | warning contains `"6"` and `"субота"` |
| 8 | Saturday marked `holiday` — no false positive | day 6 (Sat in June 2026), day_type=`holiday` | V6 | Regression | no warning for day 6 |
| 9 | Non-integer day cell skipped silently | row with day=`"травень"` alongside valid rows | AD-003 | Contract | no crash; non-integer row invisible to V4/V5 |
| 10 | Empty name after trim | `staff_list = [{"name": "", "department": "Surgery"}]` | V7 | Negative | warning contains `"порожнє"` |
| 11 | Name with invalid characters | `name = "Dr@Smith!"` | V7 | Negative | warning contains `"недопустимі"` |
| 12 | Valid Ukrainian name — no false positive | `name = "Іваненко"` | V7 | Regression | no V7 warning |

**F1 accepted** (QA finding 2026-05-07): test 9 covers the silent-skip contract for non-integer day values.

---

## Modified / new files

| File | Change |
|---|---|
| `schedule_validator.py` | NEW — validation logic |
| `bot_hook.py` | Call validator; append warnings to reply |
| `data/schedule_mapping.json.example` | Add `scheduler_date_column` |
| `google_sheets_adapter.py` | Trim `name` and `department` in `get_staff_list` |
| `tests/test_schedule_validator.py` | NEW — unit tests for all 7 checks |

---

## Open Questions

None — all inputs confirmed by Owner 2026-05-07.

---

## Sign-off

| Role | Date | Status |
|---|---|---|
| Architect | 2026-05-08 | ✅ AD-S006b2-008 added — unified message format; ready for Developer |
| Developer | — | ⏸ |
| QA | — | ⏸ |
| Owner | — | ⏸ UAT pending |
