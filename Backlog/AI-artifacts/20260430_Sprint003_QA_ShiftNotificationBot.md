# Sprint 003 — QA Review & UAT Checklist
**Sprint:** 003  
**Role:** QA Engineer  
**Date:** 2026-04-30 (re-review after Developer fixes)  
**Status:** ✅ PASS — all bugs and findings resolved. Ready for Owner UAT.  
**Dev ref:** [`20260430_Sprint003_DEV_ShiftNotificationBot.md`](20260430_Sprint003_DEV_ShiftNotificationBot.md)  
**Arch ref:** [`20260430_Sprint003_ARCH_ShiftNotificationBot.md`](20260430_Sprint003_ARCH_ShiftNotificationBot.md)

---

## Re-Review Summary

All four bugs from the first QA pass (BUG-001 through BUG-004) are fixed and verified by automated tests. 63/63 tests pass. One documentation inconsistency found in the ARCH artifact (see ARCH-DOC-001 below). Three tech debt items remain open by Developer decision (TD-001/002/003).

---

## Review Scope

| Module                               | Unit tests   | Review |
|--------------------------------------|--------------|--------|
| `messenger/telegram_adapter.py`      | ✅ 6 tests    | ✅      |
| `main._format_message()`             | ✅ 11 tests   | ✅      |
| `main.run_production()`              | ❌ 0 tests    | ✅      |
| `main.run_health()` — Telegram check | —            | ✅      |
| `cli.py` — `--date` flag             | ✅ 3 tests    | ✅      |
| `schedule_parser.load_mapping()`     | ✅ (existing) | ✅      |

---

## Bug Verification

### BUG-001 — Double period on names ending with `.` → ✅ FIXED

**Fix:** `raw_prev.rstrip(".")` strips trailing period from prev name before template inserts it. Template always appends one `.` — so "Петренко А.С." → "Петренко А.С" + "." = "Петренко А.С." in output.

**Verified by:**
- `test_no_double_period_for_name_ending_with_period` — asserts `"А.С.."` not in message and `"А.С."` is present ✅
- `test_full_message_structure` — expected value corrected to `"замість Петренко А.С.\n"` (single period) ✅

---

### BUG-002 — `--employee` filter scope → ✅ FIXED

**Fix:** `compute_contexts(shifts)` now called before the `--employee` filter. Prev/next are resolved from the full set of today's shifts; filter then selects which contexts to send.

**Verified by:** Code review of `main.py:185–188`. Test coverage gap remains open as TD-002.

---

### BUG-003 — Sends all month's shifts, not just today → ✅ FIXED

**Fix:** `run_production()` filters `all_shifts` to `shift_date == target_date` before any processing. `target_date` defaults to `date.today()` or is overridden by `--date`.

**Verified by:** Code review of `main.py:174–179`. Orchestrator test coverage gap remains open as TD-001.

---

### BUG-004 — No rate limiting between Telegram sends → ✅ FIXED

**Fix:** `time.sleep(1)` executed after each successful send. Sleep is on success path only — failed sends do not incur delay (they are logged and counted, run continues).

**Verified by:** Code review of `main.py:210`. No automated test; runtime behavior.

---

## New Feature Verification

### AD-006 — Configurable `shift_hours` → ✅ PASS

- `schedule_mapping.json.example` updated with `shift_hours` block ✅
- `data/schedule_mapping.json` updated with `shift_hours` block — GAP-004 fixed ✅
- `load_mapping()` validates each value against `HH:MM` regex; exits 1 on invalid format ✅
- `_shift_hours(config)` merges mapping values over built-in defaults — partial override supported ✅
- `_format_message(ctx, shift_hours)` uses `shift_hours.get(day_type, "09:00")` — unknown day_type falls back safely ✅
- `test_custom_shift_hours_used` verifies custom labor time overrides default ✅
- Existing tests updated to pass `HOURS` dict — no calls use stale zero-arg signature ✅

### AD-001 — `--date` CLI flag → ✅ PASS

- Flag declared in `cli.py:19–20` with `YYYY-MM-DD` metavar ✅
- Rejected without `--production` (exit 2) ✅
- Invalid format rejected at parse time (exit 2) ✅
- Valid value stored in `RunMode.date` and passed through to `run_production()` ✅
- `test_production_date`, `test_date_without_production_exits`, `test_date_invalid_format_exits` — all pass ✅

---

## Finding — GAP-004 — `shift_hours` missing from live IT config file (Severity: Medium)

**File:** `data/schedule_mapping.json`

`data/schedule_mapping.json.example` was updated with the `shift_hours` block per AD-006. The live IT-managed file `data/schedule_mapping.json` was not updated.

**Impact:** No runtime error — `_shift_hours()` falls back to `_DEFAULT_SHIFT_HOURS` when the key is absent. However, IT has no visible `shift_hours` entry in their real config file and cannot discover or use the feature without separately consulting the `.example`.

**Fix:** `shift_hours` block with default values added to `data/schedule_mapping.json`. Verified by file inspection.

**Status:** ✅ Fixed.

---

## Finding — ARCH-DOC-001 (Documentation Only)

**Location:** `20260430_Sprint003_ARCH_ShiftNotificationBot.md` — Module Contracts section, last line.

**Issue:** Contract listed as `_format_message(ctx: ShiftContext) -> str` — one parameter. AD-006 added `shift_hours: dict` as a required second parameter. The body of the ARCH correctly describes `_format_message(ctx, shift_hours)` receives the dict, but the Module Contracts section was not updated.

**Severity:** Documentation only. No code defect.

**Fix:** ARCH Module Contracts corrected to `_format_message(ctx: ShiftContext, shift_hours: dict) -> str` with note referencing AD-006. ARCH AD-006 scope updated to include `data/schedule_mapping.json`. Verified by file inspection.

**Status:** ✅ Fixed.

---

## Open Tech Debt (Accepted by Developer)

| ID     | Description                                                                               | Severity | Status   |
|--------|-------------------------------------------------------------------------------------------|----------|----------|
| TD-001 | `run_production()` orchestrator has no tests — dedup, send, record, error path (GAP-001) | Medium   | Deferred |
| TD-002 | `--employee` filter behavior not covered by integration test (GAP-002)                    | Low      | Deferred |
| TD-003 | `--force` flag behavior not covered by test (GAP-003)                                     | Low      | Deferred |
| TD-004 | Date column returns integer `1` for real XLSX — day-of-month format not yet supported     | Medium   | NTD — Owner accepted at S002 UAT |

---

## Observations (No Action Required)

**`run_health()` requires network access.**  
Telegram `getMe` is called during health check. A new install with placeholder token will show `[TELEGRAM] ❌` even if DB and XLSX are correctly configured. Correct behavior — IT should be aware the health check requires real credentials.

**`замість -.` when no predecessor.**  
When prev is absent the message reads "заступає на зміну замість -." — grammatically awkward but matches the spec ("-" substituted, line not omitted). Owner decision.

**`_format_message` imported directly in tests.**  
Tests import `_format_message` from `main`. Works because `main.py` has no import-time side effects. Acceptable for POC.

---

## UAT Checklist — Owner Executes

> Prerequisites: `.env` configured with real `TELEGRAM_BOT_TOKEN` and `TELEGRAM_GROUP_CHAT_ID`. `data/schedule.xlsx` and `data/schedule_mapping.json` in place. Run `docker compose build` first.

| #   | Action                                                  | Expected result                                                                              | Pass/Fail | Notes |
|-----|---------------------------------------------------------|----------------------------------------------------------------------------------------------|-----------|-------|
| U01 | `python main.py`                                        | All lines ✅ including `[TELEGRAM] ✅ bot reachable`                                          |           |       |
| U02 | `python main.py --dry-run`                              | Each shift block shows employee, date, prev, next, message preview. No Telegram send.        |           |       |
| U03 | `python main.py --production`                           | Messages appear in group for today only; `[PRODUCTION] sent=N skipped=0 failed=0`           |           |       |
| U04 | `python main.py --production` (second run same day)     | `[PRODUCTION] sent=0 skipped=N failed=0` — dedup prevents resend                            |           |       |
| U05 | Verify message format in Telegram group                 | `Зміна: DD-MM-YYYY` / name line / blank / `Наступна зміна:` / date + time — Сидоренко В.М. |           |       |
| U06 | Names with initials (e.g. Іваненко О.В.)               | Single period after name in "замість" line — no double period                                |           |       |
| U07 | `python main.py --production --employee "Ім'я"`         | Only that person's message sent                                                              |           |       |
| U08 | `python main.py --production --date YYYY-MM-DD`         | Messages sent for the specified date, not today                                              |           |       |
| U09 | `python main.py --reload-schedule` then `--production`  | All today's shifts resent                                                                    |           |       |
| U10 | `python main.py --production --force`                   | All shifts resent regardless of dedup                                                        |           |       |
| U11 | Edit `schedule_mapping.json` — change `labor` to `16:00` | Dry-run message shows `16:00` instead of `17:00`                                            |           |       |
| U12 | Verify log file written                                 | `data/logs/shift_bot_*.log` exists with send records                                         |           |       |

---

## Sprint 003 Sign-off

| Role        | Name | Date       | Status                                        |
|-------------|------|------------|-----------------------------------------------|
| Developer   | AI   | 2026-04-30 | ✅                                             |
| QA Engineer | AI   | 2026-04-30 | ✅ PASS — all findings resolved, ready for UAT |
| **Owner**   |      |            | ⏸ Awaiting UAT                                |
