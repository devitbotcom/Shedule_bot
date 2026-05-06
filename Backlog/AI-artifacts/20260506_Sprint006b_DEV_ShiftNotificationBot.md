# Sprint S006b — Developer Handoff Artifact
**Date:** 2026-05-06  
**Sprint:** S006b — Schedule Generation  
**Status:** ✅ READY FOR QA

---

## Deliverables completed

| ID  | Deliverable                        | File(s)                                                                              | Status |
|-----|------------------------------------|--------------------------------------------------------------------------------------|--------|
| D1  | Schedule generator                 | `schedule_generator.py`                                                              | ✅     |
| D2  | Adapter additions                  | `google_sheets_adapter.py`                                                           | ✅     |
| D3  | Key rename                         | `google_sheets_adapter.py`, `data/schedule_mapping.json.example`                     | ✅     |
| D4  | Config additions                   | `data/schedule_mapping.json.example`                                                 | ✅     |
| D5  | `/draft` command                   | `bot_hook.py`                                                                        | ✅     |
| D6  | Readme update                      | `readme_GOOGLE_SHEETS.md`                                                            | ✅     |
| D7  | Tests                              | `tests/test_schedule_generator.py`, `tests/test_google_sheets_adapter.py`, `tests/test_webhook_routing.py` | ✅     |

---

## Test results

```
135 passed in 0.79s
```

- 120 pre-existing tests: all green (zero regressions)
- 15 new tests: all green
  - 7 `test_schedule_generator.py`
  - 3 `test_google_sheets_adapter.py` (adapter additions)
  - 5 `test_webhook_routing.py` (`/draft` routing)

---

## Files changed

### New files
- `schedule_generator.py` — `generate_schedule(staff_list, template_grid, mapping) → list[list]`; `UA_MONTHS` Ukrainian month name → int mapping
- `tests/test_schedule_generator.py` — 7 tests: assignment, round-robin distribution, empty day-type row skip, empty grid, unknown department, immutability

### Modified files
- `google_sheets_adapter.py` — added `read_cell(sheet_id, tab_name, cell, credentials_path) → str`; added `write_schedule_grid(sheet_id, tab_name, rows, credentials_path) → None` (creates tab if absent, clears and overwrites if present)
- `bot_hook.py` — added `/draft` command (Head role only); added `_cmd_draft()` helper; updated `/help` to show `/draft` for Head
- `data/schedule_mapping.json.example` — renamed `staff_tab` → `scheduler_staff_tab`, `schedule_tab` → `scheduler_schedule_tab`; added `scheduler_output_tab`, `scheduler_month_cell`, `scheduler_year_cell`
- `readme_GOOGLE_SHEETS.md` — Step 4: Viewer → Editor; Step 6: updated key names and new keys
- `tests/test_google_sheets_adapter.py` — added 3 tests: `read_cell` value, `write_schedule_grid` overwrite, `write_schedule_grid` create
- `tests/test_webhook_routing.py` — added 5 tests: `/draft` denied for pending, `/draft` denied for staff, `/draft` dispatches to `_cmd_draft` for Head, `/help` shows `/draft` for Head, `/help` hides `/draft` for pending

---

## Architecture decisions implemented

| AD             | Decision                                                                                           |
|----------------|----------------------------------------------------------------------------------------------------|
| AD-S006b-001   | `/draft` triggers generation; Head role only; bot replies with confirmation                        |
| AD-S006b-002   | Month/year read from Draft tab cells A1/B1; Ukrainian month name mapped via `UA_MONTHS`            |
| AD-S006b-003   | `schedule_mapping.json` keys renamed and extended; all scheduler keys prefixed `scheduler_`        |
| AD-S006b-004   | `read_cell()` and `write_schedule_grid()` added to `google_sheets_adapter.py`                      |
| AD-S006b-005   | Weighted greedy algorithm: lowest assignment count per department; tie-break by list order          |
| AD-S006b-006   | `readme_GOOGLE_SHEETS.md` Step 4 updated to Editor permission                                     |
| AD-S006b-007   | Draft tab structure assumed correct (error prevention deferred)                                    |

---

## Prerequisites before UAT (IT setup additions)

1. Update service account permission on the Google Sheet from **Viewer** to **Editor**
2. Update `data/schedule_mapping.json` on the server — rename `staff_tab`/`schedule_tab` keys, add new scheduler keys (see `schedule_mapping.json.example`)
3. Ensure `Draft` tab exists in the Google Sheet with month in A1, year in B1, and day-type column pre-populated
4. Set Head user role via `/setrole` so `/draft` command is accessible

---

## Sprint Sign-off

| Role      | Date       | Status              |
|-----------|------------|---------------------|
| Architect | 2026-05-06 | ✅                   |
| Developer | 2026-05-06 | ✅ Ready for QA      |
| QA        | —          | ⏸                   |
| Owner     | —          | ⏸                   |
