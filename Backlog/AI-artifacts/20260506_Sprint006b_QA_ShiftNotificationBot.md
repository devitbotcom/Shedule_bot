# Sprint S006b — QA Delivery Report
**Date:** 2026-05-06  
**Role:** QA  
**Sprint:** S006b — Schedule Generation  
**Scope:** 15 new tests across 3 files; 3 modified + 2 new source files  
**Suite status:** 135/135 passing (120 pre-existing + 15 new)

---

## Legend

### Design techniques

| Term | Meaning                                                                                                        |
|------|----------------------------------------------------------------------------------------------------------------|
| **EP** — Equivalence Partitioning | Input space divided into partitions where all values behave the same. One representative per partition tested. |
| **State-based** | Verifies system state before and after an operation.                                                           |
| **Negative** | Provides invalid or forbidden input and verifies the system rejects it correctly.                              |
| **Contract** | Verifies a non-functional guarantee: correct call target, no crash, no mutation.                               |
| **Regression** | Written specifically to prevent a known past bug or design invariant from regressing.                          |
| **Idempotency** | Verifies that running the same operation twice produces the same result as once.                               |

---

## Coverage by file

| File                                  | Tests  | Notes                                                              |
|---------------------------------------|--------|--------------------------------------------------------------------|
| `tests/test_schedule_generator.py`    | 7      | Algorithm correctness, round-robin, immutability — ✅ in scope      |
| `tests/test_google_sheets_adapter.py` | +3     | `read_cell`, `write_schedule_grid` overwrite + create — ✅ in scope |
| `tests/test_webhook_routing.py`       | +5     | `/draft` role gate, dispatch, `/help` visibility — ✅ in scope      |

---

## Test table — test_schedule_generator.py

| #  | Test                                               | Main purpose                                   | Design technique  | Redundant / inefficient |
|----|----------------------------------------------------|------------------------------------------------|-------------------|-------------------------|
| 1  | `test_ua_months_complete`                          | 12 entries, boundary values correct            | EP                | ✅                       |
| 2  | `test_generate_assigns_staff_to_departments`       | Staff assigned per department, correct mapping | EP, State-based   | ✅                       |
| 3  | `test_generate_round_robin_distributes_evenly`     | Weighted greedy produces equal distribution    | State-based       | ✅                       |
| 4  | `test_generate_skips_rows_with_empty_day_type`     | Empty day-type rows skipped, others filled     | Negative          | ✅                       |
| 5  | `test_generate_empty_grid_returns_empty`           | Empty input returns empty                      | EP (boundary)     | ✅                       |
| 6  | `test_generate_unknown_department_column_no_crash` | Unknown dept col in mapping — no crash         | Negative          | ✅                       |
| 7  | `test_generate_does_not_mutate_input`              | Input grid unchanged after call                | Contract          | ✅                       |

## Test table — test_google_sheets_adapter.py (new tests only)

| # | Test                                               | Main purpose                                             | Design technique  | Redundant / inefficient |
|---|----------------------------------------------------|----------------------------------------------------------|-------------------|-------------------------|
| 8 | `test_read_cell_returns_string_value`              | Correct cell address forwarded; value returned as string | Contract          | ✅                       |
| 9 | `test_write_schedule_grid_overwrites_existing_tab` | `clear()` + `update()` called on existing tab            | Contract          | ✅                       |
| 10 | `test_write_schedule_grid_creates_tab_if_absent`   | `add_worksheet()` called when tab missing                | Contract          | ✅                       |

## Test table — test_webhook_routing.py (new tests only)

| #  | Test                                  | Main purpose                                 | Design technique  | Redundant / inefficient |
|----|---------------------------------------|----------------------------------------------|-------------------|-------------------------|
| 11 | `test_draft_denied_for_pending`       | Role gate blocks pending                     | Negative          | ✅                       |
| 12 | `test_draft_denied_for_staff`         | Role gate blocks staff                       | Negative          | ✅                       |
| 13 | `test_draft_calls_cmd_draft_for_head` | `/draft` dispatches to `_cmd_draft` for Head | Contract          | ✅                       |
| 14 | `test_help_shows_draft_for_head`      | `/help` lists `/draft` for Head              | EP                | ✅                       |
| 15 | `test_help_hides_draft_for_pending`   | `/help` does not list `/draft` for pending   | Negative          | ✅                       |

---

## Findings

| ID  | Severity  | Location                                                        | Description                                                                                                                                                                                                                                                                                                                                                                             |
|-----|-----------|-----------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| F1  | 🟡 Minor  | `20260506_Sprint006b_ARCH_ShiftNotificationBot.md` AD-S006b-005 | ARCH specifies `generate_schedule(staff_list, template_grid, month, year)` — implementation correctly uses `generate_schedule(staff_list, template_grid, mapping)`. `month`/`year` are unused by the algorithm (structure is in the template grid); `mapping` is needed for `header_row`, `day_type_column`, `department_columns`. ARCH spec must be corrected to match implementation. **Fixed — Architect corrected AD-S006b-005 2026-05-07.** |
| F2  | 🟡 Minor  | `tests/test_webhook_routing.py`                                 | `_cmd_draft` internals not tested. Routing test only verifies dispatch. Error paths — missing env vars, unrecognised month name, gspread failure — have no test coverage. Breaches quality primitive: **Maintainability / Testability** — "Unit tests cover all logic layers." **Fixed — `tests/test_cmd_draft.py` added 2026-05-07: 6 tests covering all error paths + happy path. 141/141 passing.** |
| F3  | 🔵 Low    | `readme_GOOGLE_SHEETS.md` Troubleshooting table                 | `WorksheetNotFound` row still references `staff_tab` / `schedule_tab`. These keys were renamed to `scheduler_staff_tab` / `scheduler_schedule_tab` in D3. Stale after rename. **Fixed — troubleshooting table updated 2026-05-07.** |
| F4  | 🔵 Low    | `20260506_Sprint006b_ARCH_ShiftNotificationBot.md` OQ-1         | OQ-1 ("Which file owns `/draft` routing?") resolved by Developer (`bot_hook.py`) but ARCH still shows ⏸. **Fixed — Architect marked OQ-1 resolved 2026-05-07.** |

---

## Architecture decisions — verification

| AD           | Claim                                                               | Verified                                                                 |
|--------------|---------------------------------------------------------------------|--------------------------------------------------------------------------|
| AD-S006b-001 | `/draft` Head-only; reads Sheet; generates; writes; replies         | ✅ Code + routing tests 11–13                                             |
| AD-S006b-002 | Month/year from Draft tab A1/B1; `UA_MONTHS` mapping                | ✅ Code + test 1                                                          |
| AD-S006b-003 | Config keys renamed + 3 new keys in `schedule_mapping.json.example` | ✅ Confirmed in file                                                      |
| AD-S006b-004 | `read_cell()` + `write_schedule_grid()` added to adapter            | ✅ Code + tests 8–10                                                      |
| AD-S006b-005 | `generate_schedule` signature                                       | ✅ F1 fixed — ARCH corrected 2026-05-07 |
| AD-S006b-006 | `readme_GOOGLE_SHEETS.md` Step 4 Viewer → Editor                    | ✅ Confirmed                                                              |
| AD-S006b-007 | Draft tab structure assumed correct; error prevention deferred      | ✅ Confirmed                                                              |

---

## Overall verdict

**✅ ACCEPTED — all findings resolved. UAT pending.**

141/141 passing. Zero regressions.

**UAT doc:** `20260507_Sprint006b_UAT_ShiftNotificationBot.md`

---

## Sprint sign-off

| Role      | Date       | Status                                |
|-----------|------------|---------------------------------------|
| Architect | 2026-05-06 | ✅                                     |
| Developer | 2026-05-06 | ✅                                     |
| QA        | 2026-05-07 | ✅ All findings resolved — UAT pending |
| Owner     | —          | ⏸ UAT pending                         |
