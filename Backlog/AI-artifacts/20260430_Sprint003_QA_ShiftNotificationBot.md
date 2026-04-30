# Sprint 003 — QA Review & UAT Checklist
**Sprint:** 003  
**Role:** QA Engineer  
**Date:** 2026-04-30  
**Status:** ❌ FAIL — 2 bugs, 3 test gaps. Must fix before UAT.  
**Dev ref:** [`20260430_Sprint003_DEV_ShiftNotificationBot.md`](20260430_Sprint003_DEV_ShiftNotificationBot.md)

---

## Review Scope

| Module                               | Unit tests  | Review  |
|--------------------------------------|-------------|---------|
| `messenger/telegram_adapter.py`      | ✅ 6 tests   | ✅       |
| `main._format_message()`             | ✅ 9 tests   | ✅       |
| `main.run_production()`              | ❌ 0 tests   | ✅       |
| `main.run_health()` — Telegram check | —           | ✅       |

---

## Bugs

### BUG-001 — Double period when staff name ends with `.` (Severity: ON HOLD)

**File:** `main.py:59`, `tests/test_format_message.py:85`

The message line:
```python
f"{s.employee_name} заступає на зміну замість {prev_name}.\n"
```
When `prev_name = "Петренко А.С."` the output is:
```
Іваненко О.В. заступає на зміну замість Петренко А.С..
```
Double period. Ukrainian staff names commonly end in initials — this will affect the majority of real messages.

**Worse:** `test_full_message_structure` hardcodes the double-period output as the expected value (`"Петренко А.С.."`), so the test passes and hides the bug.

**Fix required:** Strip trailing period from `prev_name` before inserting, or remove the trailing `.` from the format string and add it only when `prev_name` does not already end with `.`.

---

### BUG-002 — `--employee` filter applied before `compute_contexts()` (Severity: Medium)

**File:** `main.py:161–167`

```python
if run_mode.employee:
    shifts = [s for s in shifts if s.employee_name == run_mode.employee]
...
contexts = compute_contexts(shifts)
```

Filtering before `compute_contexts()` means prev/next colleagues are computed only within the filtered set.
If Alice has one shift, her message shows `замість -.` and `Наступна зміна: -` even though the full schedule has a predecessor and successor.

**Expected:** `--employee` restricts *which messages are sent*, not how prev/next is computed. Filter must be applied after `compute_contexts()`.



### BUG-003 - UAT discovered. System sends all messages at once, despite dates [CRITICAL]

STR:
docker compose run --rm bot python main.py --production
2026-04-30 19:05:15,861 [INFO] Starting shift_bot | mode=production


Actual: Message appears in group. BUT. The system sens all messages from the source.

Expected:
ARCHITECT to review. Likely we have a gap in requirements.

### BUG-004 - UAT discovered. System sends all messages at once, despite dates [HIGH]

STR:
docker compose run --rm bot python main.py --production
2026-04-30 19:05:15,861 [INFO] Starting shift_bot | mode=production


Actual: System loads 3rd party with no debounce.

Expected:
ARCHITECT to propose reasonable solution. Add to Quality acceptance characteristics.

---

## Test Gaps

### GAP-001 — `run_production()` orchestrator not tested

No test verifies:
- Shift already notified → skipped, not sent
- Send succeeds → `record_notification(status='ok')` called
- Send fails → `record_notification(status='fail')` called, run continues
- All fail → exit code 1
- Zero failures → exit code 0

### GAP-002 — `--employee` filter not tested

No test verifies that `--production --employee "Alice"` sends only Alice's shift and not Bob's.

### GAP-003 — `--force` flag not tested

No test verifies that `--force` resends an already-notified shift.

---

## Observations (No Action Required)

**`run_health()` now requires network access.**  
Telegram `getMe` is called during health check. A new install with placeholder token will show `[TELEGRAM] ❌` even if DB and XLSX are correctly configured. This is correct behavior — the bot cannot work without a valid token — but IT should be aware the health check now requires real credentials.

**`test_format_message.py` imports `_format_message` from `main`.**  
Works correctly because `main.py` has no import-time side effects. Acceptable for POC.

---

## UAT Checklist — Owner Executes

> Prerequisites: `.env` configured with a real `TELEGRAM_BOT_TOKEN` and `TELEGRAM_GROUP_CHAT_ID`. `data/schedule.xlsx` and `data/schedule_mapping.json` in place. Run `docker compose build` first.

| #   | Action                                                 | Expected result                                                                  | Pass/Fail  | Notes  |
|-----|--------------------------------------------------------|----------------------------------------------------------------------------------|------------|--------|
| U01 | `python main.py`                                       | All lines ✅ including `[TELEGRAM] ✅ bot reachable`                               |            |        |
| U02 | `python main.py --dry-run`                             | Each shift block shows employee, date, prev, next, and message preview           |            |        |
| U03 | `python main.py --production`                          | Messages appear in Telegram group; `[PRODUCTION] sent=N skipped=0 failed=0`      |            |        |
| U04 | `python main.py --production` (second run)             | `[PRODUCTION] sent=0 skipped=N failed=0` — dedup prevents resend                 |            |        |
| U05 | Verify DB after production run                         | `notifications` table has one `ok` record per shift                              |            |        |
| U06 | Verify log file written                                | `data/logs/shift_bot_*.log` exists with send records                             |            |        |
| U07 | Verify message format in group                         | Format matches: `Зміна: DD-MM-YYYY` / name line / blank / `Наступна зміна:` line |            |        |
| U08 | `python main.py --production --employee "Name"`        | Only that person's message sent to group                                         |            |        |
| U09 | `python main.py --reload-schedule` then `--production` | All shifts resent                                                                |            |        |
| U10 | `python main.py --production --force`                  | All shifts resent regardless of dedup                                            |            |        |

---

## Sprint 003 Sign-off

| Role        | Name  | Date       | Status                                  |
|-------------|-------|------------|-----------------------------------------|
| Developer   | AI    | 2026-04-30 | ✅                                       |
| QA Engineer | AI    | 2026-04-30 | ❌ Fail — BUG-001, BUG-002 must be fixed |
| **Owner**   |       |            | ⏸ Blocked on QA pass                    |
