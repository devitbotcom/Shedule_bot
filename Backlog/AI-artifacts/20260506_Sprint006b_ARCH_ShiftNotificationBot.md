# Sprint S006b — Architecture

**Sprint:** S006b  
**Role:** Architect  
**Date:** 2026-05-06  
**Status:** ⏸ READY FOR DEVELOPER  
**Depends on:** S006a UAT accepted  
**Blocks:** S006c (Head preferences / constraints)

---

## Sprint Goal

Bot generates a full-month duty schedule using a weighted greedy algorithm, writes the result to a `Draft-by-bot` tab in the Google Sheet, and confirms to Head. Head triggers generation via `/draft` Telegram command. The notification pipeline (POC1) is untouched.

**Dev/QA sheet (public, no real data):** https://docs.google.com/spreadsheets/d/1lKX5ntqGN2UPf9LSDDKJTsGKtHmQiPK2BhtS61OCWv0/edit?usp=sharing

---

## Scope

| In                                                                               | Out                                          |
|----------------------------------------------------------------------------------|----------------------------------------------|
| Weighted greedy schedule generation algorithm                                    | AI-generated schedule                        |
| Read month/year from Google Sheet (Draft tab A1/B1)                              | Head preferences / blackout days (S006c)     |
| Read staff list from `Staff` tab                                                 | Writing to `schedule.xlsx`                   |
| Read day types from `Draft` tab                                                  | Notification pipeline (untouched)            |
| Write filled schedule to `Draft-by-bot` tab (create if absent, overwrite)        | Google Drive auth for prod (later)           |
| `/draft` Telegram command (Head role only)                                       | Multi-location                               |
| Rename `staff_tab`/`schedule_tab` keys (feedback 06-01)                          |                                              |
| Update service account permission: Viewer → Editor                               |                                              |
| Tests                                                                            |                                              |

---

## Key Architectural Decisions

### AD-S006b-001 — `/draft` command triggers generation

Head sends `/draft` to the bot. The bot:
1. Reads month and year from the Google Sheet (`Draft` tab, cells A1 and B1)
2. Runs the generation algorithm
3. Writes the result to the `Draft-by-bot` tab
4. Replies to Head: `"Draft for <місяць> <рік> written to Draft-by-bot"`

No month/year argument is passed in the command — the Sheet is the single source of truth for which period to generate.

**Role gate:** Head role only. IT and Staff receive "access denied".

---

### AD-S006b-002 — Month/year from Google Sheet cells

Month and year are read from the `Draft` tab:

| Cell | Content  | Format                               |
|------|----------|--------------------------------------|
| A1   | Month    | Ukrainian text name — e.g. `червень` |
| B1   | Year     | String — e.g. `2026`                 |

Ukrainian month name → integer mapping built into `schedule_generator.py`:

```python
UA_MONTHS = {
    "січень": 1, "лютий": 2, "березень": 3, "квітень": 4,
    "травень": 5, "червень": 6, "липень": 7, "серпень": 8,
    "вересень": 9, "жовтень": 10, "листопад": 11, "грудень": 12
}
```

Cell references are IT-configurable via `schedule_mapping.json` (`scheduler_month_cell`, `scheduler_year_cell`).

---

### AD-S006b-003 — `schedule_mapping.json` additions

Five keys added (three new, two renamed from S006a feedback 06-01):

```json
{
  "scheduler_staff_tab":      "Staff",
  "scheduler_schedule_tab":   "Draft",
  "scheduler_output_tab":     "Draft-by-bot",
  "scheduler_month_cell":     "A1",
  "scheduler_year_cell":      "B1"
}
```

Old keys `staff_tab` and `schedule_tab` are removed from config and code.

---

### AD-S006b-004 — `google_sheets_adapter.py` additions

Two new functions added to the existing adapter:

```python
def read_cell(sheet_id: str, tab_name: str, cell: str, credentials_path: str) -> str:
    """Returns the string value of a single cell (e.g. 'A1')."""

def write_schedule_grid(sheet_id: str, tab_name: str, rows: list[list], credentials_path: str) -> None:
    """Writes rows to tab_name. Creates the tab if it does not exist; clears and overwrites if it does."""
```

`write_schedule_grid` uses `gspread` worksheet `clear()` + `update()`. Tab creation uses `add_worksheet()`.

---

### AD-S006b-005 — Weighted greedy algorithm

New file `schedule_generator.py`. Interface:

```python
def generate_schedule(
    staff_list: list[dict],       # from get_staff_list — {name, department}
    template_grid: list[list],    # from get_schedule_grid — raw 2D grid (Draft tab)
    month: int,
    year: int,
) -> list[list]:
    """Returns filled grid ready to write to Draft-by-bot tab."""
```

**Algorithm:**

For each data row in `template_grid` (skipping header rows per `header_row` from `schedule_mapping.json`):
1. Read day type from the day-type column
2. For each department column: select the staff member from that department with the lowest assignment count so far
3. Tie-break: first in list order
4. Increment that staff member's count
5. Populate the row with assigned names

**Assumptions for S006b (error prevention deferred to later sprint):**
- `Draft` tab dates and day types are pre-populated correctly
- Each department has at least one staff member (realistic for hospital)

---

### AD-S006b-006 — Service account permission: Editor

Writing to Google Sheets requires **Editor** permission. `readme_GOOGLE_SHEETS.md` Step 4 updated from "Viewer" to "Editor".

---

### AD-S006b-007 — `Draft` tab structure

| Cell / Column         | Content                                                        |
|-----------------------|----------------------------------------------------------------|
| A1                    | Month — Ukrainian text name (e.g. `червень`)                   |
| B1                    | Year — string (e.g. `2026`)                                    |
| Row `header_row`      | Column headers (date, day-type, departments)                   |
| Rows below header     | One row per day; date + day-type pre-filled; staff cells empty |

---

## Developer Deliverables

| #  | Deliverable                    | File(s)                                   | Notes                                                                 |
|----|--------------------------------|-------------------------------------------|-----------------------------------------------------------------------|
| D1 | Schedule generator             | `schedule_generator.py`                   | `generate_schedule()`; `UA_MONTHS` mapping                            |
| D2 | Adapter additions              | `google_sheets_adapter.py`                | Add `read_cell()`, `write_schedule_grid()`                            |
| D3 | Key rename                     | `google_sheets_adapter.py`, `main.py`, any caller | `staff_tab`/`schedule_tab` → `scheduler_staff_tab`/`scheduler_schedule_tab` |
| D4 | Config additions               | `data/schedule_mapping.json.example`      | Add `scheduler_output_tab`, `scheduler_month_cell`, `scheduler_year_cell`; rename D3 keys |
| D5 | `/draft` command               | `webhook_handler.py` (or equivalent)      | Head role only; calls generator; writes to Sheet; replies to Head     |
| D6 | Readme update                  | `readme_GOOGLE_SHEETS.md` Step 4          | Viewer → Editor                                                       |
| D7 | Tests                          | `tests/test_schedule_generator.py`, `tests/test_google_sheets_adapter.py` | Mock gspread; cover algorithm, write, read_cell |

---

## Open Questions

| #    | Question                                                                  | Needed for  | Status                                             |
|------|---------------------------------------------------------------------------|-------------|----------------------------------------------------|
| OQ-1 | Which file / handler owns Telegram command routing for `/draft`?          | D5          | ⏸ Developer to confirm from S005 webhook structure |

---

## Sprint Sign-off

| Role      | Date       | Status                |
|-----------|------------|-----------------------|
| Architect | 2026-05-06 | ✅ Ready for Developer |
| Developer | —          | ⏸                     |
| QA        | —          | ⏸                     |
| Owner     | —          | ⏸                     |
