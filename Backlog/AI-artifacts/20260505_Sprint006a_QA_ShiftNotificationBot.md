# Sprint S006a — QA Delivery Report
**Date:** 2026-05-05 | **Revised:** 2026-05-06  
**Role:** QA  
**Sprint:** S006a — Google Sheets Integration  
**Scope:** 13 new tests across 2 new files; 5 modified source files  
**Suite status:** 126/126 passing (113 pre-existing + 13 new)

> ⚠️ **Revised 2026-05-06** — Architect confirmed D2 (`schedule_sync.py`) and D3 (`--sync-schedule`) were built on a wrong assumption. They are out of scope for POC2. QA findings F1, F2, F3 are superseded. New finding F5 registered. Verdict revised.

---

## Legend

### Design techniques

| Term                              | Meaning                                                                                                                                           |
|-----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **EP** — Equivalence Partitioning | Input space divided into partitions where all values behave the same. One representative per partition tested.                                    |
| **State-based**                   | Verifies system state before and after an operation (e.g. file written). Outcome checked by inspecting stored state, not just return value.      |
| **Negative**                      | Provides invalid or forbidden input and verifies the system rejects it correctly.                                                                 |
| **Contract**                      | Verifies a non-functional guarantee: correct call target, no crash, no mutation. The *what* is less important than the *how*.                    |
| **Regression**                    | Written specifically to prevent a known past bug or design invariant from regressing.                                                             |
| **Idempotency**                   | Verifies that running the same operation twice produces the same result as once.                                                                  |

### Redundant / inefficient column

| Symbol              | Meaning                                                                                  |
|---------------------|------------------------------------------------------------------------------------------|
| ✅                   | Clean — no overlap, no waste                                                             |
| ⚠️ Overlaps with    | Re-asserts something already covered by another test.                                    |
| ⚠️ Weak assertion   | Test passes when it should not, due to an overly broad condition.                        |

---

## Coverage by file

| File                                    | Tests | Notes                                                                   |
|-----------------------------------------|-------|-------------------------------------------------------------------------|
| `tests/test_google_sheets_adapter.py`   | 7     | Credential forwarding, tab routing, dict shape, empty filtering — ✅ in scope |
| ~~`tests/test_schedule_sync.py`~~       | ~~6~~ | ❌ Out of scope — covers code to be deleted (see F5)                    |

---

## Test table — test_google_sheets_adapter.py

| #  | Test                                                      | Main purpose                                           | Design technique | Redundant / inefficient                         |
|----|-----------------------------------------------------------|--------------------------------------------------------|------------------|-------------------------------------------------|
| 1  | `test_get_staff_list_returns_name_department_dicts`        | Two rows mapped to `{name, department}` dicts          | EP, State-based  | ✅                                               |
| 2  | `test_get_staff_list_skips_rows_with_empty_name`           | Row with empty name filtered out                       | Negative         | ✅                                               |
| 3  | `test_get_staff_list_empty_sheet`                          | Empty sheet returns `[]`                               | EP (boundary)    | ✅                                               |
| 4  | `test_get_schedule_grid_returns_2d_list`                   | Grid returned as 2D list unchanged                     | EP               | ✅                                               |
| 5  | `test_get_schedule_grid_empty_sheet`                       | Empty sheet returns `[]`                               | EP (boundary)    | ⚠️ Overlaps with #3 (same boundary, different function) |
| 6  | `test_adapter_uses_credentials_path`                       | `service_account` called with correct path             | Contract         | ✅                                               |
| 7  | `test_adapter_opens_correct_sheet_and_tab`                 | `open_by_key` and `worksheet` called with correct args | Contract         | ✅                                               |

## ~~Test table — test_schedule_sync.py~~ ❌ Out of scope

| #  | Test                                      | Status                            |
|----|-------------------------------------------|-----------------------------------|
| 8  | `test_sync_writes_xlsx`                   | ❌ Covers out-of-scope code        |
| 9  | `test_sync_exits_if_no_sheet_id`          | ❌ Covers out-of-scope code        |
| 10 | `test_sync_exits_if_no_credentials`       | ❌ Covers out-of-scope code        |
| 11 | `test_sync_prints_summary`                | ❌ Covers out-of-scope code        |
| 12 | `test_sync_uses_tab_names_from_mapping`   | ❌ Covers out-of-scope code        |
| 13 | `test_sync_overwrites_existing_xlsx`      | ❌ Covers out-of-scope code        |

---

## Findings

| ID | Severity | Location | Description |
|----|----------|----------|-------------|
| ~~F1~~ | ~~🟡 Minor~~ | ~~`cli.py:44`~~ | ~~Stale error message after `--sync-schedule` added to `_admin_modes`.~~ **Superseded by F5** — `--sync-schedule` will be removed entirely. |
| ~~F2~~ | ~~🔵 Low~~ | ~~`schedule_sync.py:39`~~ | ~~`get_staff_list` called after XLSX written.~~ **Superseded by F5** — `schedule_sync.py` will be deleted. |
| ~~F3~~ | ~~🔵 Low~~ | ~~`tests/test_cli.py`~~ | ~~No tests for `--sync-schedule`.~~ **Superseded by F5** — `--sync-schedule` will be removed. |
| F4 | 🔵 Low | `20260505_Sprint006a_ARCH_ShiftNotificationBot.md` (AD-S006a-003) | ARCH spec declared `get_schedule_grid` return type as `list[dict]`; implementation correctly returns `list[list]`. **Fixed** — ARCH corrected 2026-05-06. |
| F5 | 🔴 Blocker | `schedule_sync.py`, `tests/test_schedule_sync.py`, `cli.py`, `main.py`, `models.py` | D2 (`schedule_sync.py`) and D3 (`--sync-schedule`) were built on the wrong assumption that scheduling output feeds the notification pipeline. Scheduling and notifications are independent processes; the new logic has no connection to the notification pipeline. These deliverables are out of scope for POC2 and must be removed. **Architect confirmed 2026-05-06. Refactor instructions added to ARCH. Fixed — refactor complete 2026-05-06.** |
| F6 | 🔴 Blocker | missing `readme_GOOGLE_SHEETS.md` | Google Sheets service account setup has no deployment readme. IT setup steps exist only in the ARCH artifact (AD-S006a-001), which is a backlog document not a deployment guide. UAT prerequisites 3–6 cannot be completed without external knowledge. Breaches quality primitive: **Documentation / Deployment traceability** — each deployment step must be documented with expected observable outcome. **Fixed — `readme_GOOGLE_SHEETS.md` created 2026-05-06.** |

---

## Architecture decisions — verification

| AD           | Claim                                                               | Verified                                                                                                                  |
|--------------|---------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| AD-S006a-001 | `gspread.service_account` used; no user interaction                 | ✅ Confirmed in code and test #6                                                                                           |
| AD-S006a-002 | Tab names from `schedule_mapping.json`                              | ✅ Confirmed in code and test #12 (adapter test)                                                                          |
| AD-S006a-003 | Adapter interface — `get_staff_list` list[dict]; `get_schedule_grid` list[list] | ✅ Correct. F4 (spec type hint) fixed in ARCH.                                                              |
| ~~AD-S006a-004~~ | ~~`schedule_sync` writes XLSX~~                                 | ❌ Out of scope — wrong assumption; to be removed (F5)                                                                    |
| ~~AD-S006a-005~~ | ~~`--sync-schedule` flag~~                                      | ❌ Out of scope — wrong assumption; to be removed (F5)                                                                    |
| AD-S006a-006 | Credentials path absolute; no credentials in git                    | ✅ Confirmed in `.env.example`                                                                                            |

---

## Overall verdict

**✅ ACCEPTED — all findings resolved. UAT pending.**

F5 resolved (refactor complete). F6 resolved (`readme_GOOGLE_SHEETS.md` created). 120/120 passing. Zero regressions.

**UAT doc:** `20260506_Sprint006a_UAT_ShiftNotificationBot.md`

---

## Sprint sign-off

| Role      | Date       | Status                              |
|-----------|------------|-------------------------------------|
| Architect | 2026-05-06 | ✅ Refactor instructions added       |
| Developer | 2026-05-06 | ✅ Refactor complete                 |
| QA        | 2026-05-06 | ✅ All findings resolved — UAT pending |
| Owner     | —          | ⏸ UAT pending                         |
