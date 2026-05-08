# Sprint S006b2 — QA Delivery Report
**Date:** 2026-05-08
**Role:** QA
**Sprint:** S006b2 — Draft Validation Warnings
**Scope:** 13 new tests in 1 new file; 3 modified + 1 new source file
**Suite status:** 156/156 passing (143 pre-existing + 13 new)

---

## Legend

| Term | Meaning |
|---|---|
| **EP** | Equivalence Partitioning |
| **Boundary** | Boundary value analysis |
| **Negative** | Invalid input, system must reject or warn |
| **Regression** | Prevents a known false positive or past bug |
| **Contract** | Verifies a non-functional guarantee (no crash, no mutation, silent skip) |

---

## Coverage by file

| File | Tests | Notes |
|---|---|---|
| `tests/test_schedule_validator.py` | 13 | All 7 checks + boundary + contract — ✅ in scope |

---

## Test table

| # | Test | Check | Technique |
|---|---|---|---|
| 1 | `test_no_warnings_valid_grid` | all | EP (valid partition) |
| 2 | `test_v1_empty_staff` | V1 | Negative |
| 3 | `test_v2_missing_day_type` | V2 | Negative |
| 4 | `test_v3_empty_day_cell` | V3 | Negative |
| 5a | `test_v4_leap_year_no_warning` | V4 | Boundary (Feb 2028, leap) |
| 5b | `test_v4_non_leap_year_warns` | V4 | Boundary (Feb 2029, non-leap) |
| 6 | `test_v5_days_out_of_order` | V5 | Negative |
| 7 | `test_v6_saturday_marked_labour` | V6 | Negative |
| 8 | `test_v6_saturday_marked_holiday_no_warning` | V6 | Regression (no false positive) |
| 9 | `test_non_integer_day_skipped_silently` | AD-003 | Contract |
| 10 | `test_v7_empty_name_warns` | V7 | Negative |
| 11 | `test_v7_invalid_chars_warns` | V7 | Negative |
| 12 | `test_v7_ukrainian_name_no_warning` | V7 | Regression (no false positive) |

---

## Findings

| ID | Severity | Location | Description |
|---|---|---|---|
| F1 | 🔵 Low | `tests/test_schedule_validator.py:6` | `import pytest` unused — no fixtures or marks. **Fixed — removed 2026-05-08.** |
| F2 | 🔵 Low | `bot_hook.py:91` | `year_int is None` skips entire validator; only V4/V6 need year — V1, V2, V3, V5, V7 could still run. Silent — user gets no feedback that validation was skipped. Accepted for this sprint; deferred to backlog. |

---

## Architecture decisions — verified

| AD | Claim | Verified |
|---|---|---|
| AD-S006b2-001 | New module `schedule_validator.py`, returns `list[str]`, no I/O | ✅ |
| AD-S006b2-002 | Never raises — each check wrapped in `try/except` | ✅ |
| AD-S006b2-003 | `scheduler_date_column` → fallback `date_column`; non-integer skipped silently | ✅ test 9 |
| AD-S006b2-004 | `weekday() >= 5`, case-insensitive `holiday`, invalid day caught | ✅ tests 7, 8 |
| AD-S006b2-005 | `⚠️ Попередження:` bullet block appended after ✅ line | ✅ code |
| AD-S006b2-006 | Validator called after data read, before `generate_schedule` | ✅ code |
| AD-S006b2-007 | `get_staff_list` trims `name` and `department` | ✅ code |

---

## UAT findings — resolved (2026-05-08)

| UAT finding | Fix | New tests |
|---|---|---|
| 06b2-3 CRITICAL — V2 not firing on empty cell | `_cell()` helper prevents `str(None)="None"`; column-not-found diagnostic added | T14, T15 |
| 06b2-1 — Mon-Fri not checked for holiday | V6b added: weekday marked `holiday` warns with Ukrainian name | T13a, T13b |
| 06b2-2 part 1 — V5 message too vague | First out-of-order position shown explicitly | T6 updated |
| 06b2-2 part 2 — warnings not in tab | Warning block appended to `filled_grid` before write | `test_cmd_draft_warnings_appended_to_grid` |

**Suite after fixes: 162/162 passing.**

**Post-UAT finding:**

| ID | Severity | Location | Description |
|---|---|---|---|
| F3 | 🔵 Low | `schedule_validator.py:126` | V5 `for…else` dead code — `else` never fires since `expected_seq` is same length as `day_numbers`. Harmless. |

## Overall verdict

**✅ ACCEPTED — UAT findings resolved. F1 fixed, F2/F3 deferred. 162/162 passing. Zero regressions.**

**UAT doc:** to be created.

---

## Sprint sign-off

| Role | Date | Status |
|---|---|---|
| Architect | 2026-05-07 | ✅ |
| Developer | 2026-05-07 | ✅ |
| QA | 2026-05-08 | ✅ UAT findings resolved; F1/F2/F3 deferred — UAT re-run pending |
| Owner | — | ⏸ UAT pending |
