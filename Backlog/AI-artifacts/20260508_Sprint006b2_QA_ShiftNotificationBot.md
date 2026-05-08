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
| `tests/test_schedule_validator.py` | 18 | All 7 checks + boundary + contract + UAT fixes — ✅ in scope |
| `tests/test_cmd_draft.py` | 7 | Happy path, error paths, warning-in-tab — ✅ in scope |

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
| 13a | `test_v6b_weekday_marked_holiday_warns` | V6b | Negative (UAT 06b2-1) |
| 13b | `test_v6b_weekday_marked_labour_no_warning` | V6b | Regression (no false positive) |
| 14a | `test_missing_date_column_warns` | column diagnostic | Negative (UAT 06b2-3) |
| 14b | `test_missing_day_type_column_warns` | column diagnostic | Negative (UAT 06b2-3) |
| 15 | `test_v2_fires_when_cell_is_none` | V2 + `_cell()` | Regression (UAT 06b2-3 root cause) |

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
| 06b2-2 part 1 (round 1) — V5 message too vague | Showed "позиція {pos}" — Owner rejected: internal number, not visible in sheet | T6 updated (rejected) |
| 06b2-2 part 1 (round 2) — V5 message still unreadable | Message changed to "після дня {prev} очікувався день {exp}, знайдено {actual}" — actual day numbers visible in spreadsheet | T6 re-asserts against day numbers |
| 06b2-2 part 2 — warnings not in tab | Warning block appended to `filled_grid` before write | `test_cmd_draft_warnings_appended_to_grid` |

**Suite after all fixes: 164/164 passing** (includes 06b-04 initials fix + 2 new tests).

**Post-UAT findings:**

| ID | Severity | Location | Description |
|---|---|---|---|
| F3 | 🔵 Low | `schedule_validator.py` | V5 `for…else` dead code. **Fixed — removed 2026-05-08.** |
| F4 | 🟡 Low | `tests/test_schedule_validator.py:78` | `test_v4_leap_year_no_warning` asserts `"має бути"` — stale text after AD-S006b2-008. Test passes but assertion no longer guards V4 false positives. **Open — Developer to fix.** |
| F5 | 🟡 Low | `schedule_validator.py` V6 | Inner `except (ValueError, OverflowError)` does not catch `TypeError`. If `year_int=None` reaches `date()`, V6/V6b silently aborts. Production safe (bot_hook guards). **See KI-004.** |
| F6 | 🟡 Low | `schedule_validator.py` V3 | Missing date column causes V3 to cascade: `[Структура] N рядків` fires alongside `[Налаштування]` warning. Noise only — root cause clear from tag. **See KI-005.** |

**Logic review verdict:** all 7 checks logically correct. No false positives in normal operation. F5/F6 are latent edge cases, not production bugs.

## Overall verdict

**✅ ACCEPTED — UAT findings and 06b-04 resolved. F4 open (test quality). F2/F5/F6 deferred to KI. 164/164 passing. Zero regressions.**

KI document: `Backlog/AI-artifacts/20260508_KnownIssues_ShiftNotificationBot.md`

---

## Sprint sign-off

| Role | Date | Status |
|---|---|---|
| Architect | 2026-05-08 | ✅ AD-S006b2-008 added |
| Developer | 2026-05-08 | ✅ |
| QA | 2026-05-08 | ✅ Logic review done; F4 open; KI published |
| Owner | — | ⏸ UAT re-run pending (U006b2-2, U006b2-3) |
