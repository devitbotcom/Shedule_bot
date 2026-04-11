# Sprint 002 — Test Plan & UAT Checklist
**Sprint:** 002  
**Role:** QA Engineer  
**Date:** 2026-04-05  
**Status:** ✅ READY  
**Arch ref:** [`20260405_Sprint002_ARCH_ShiftNotificationBot.md`](20260405_Sprint002_ARCH_ShiftNotificationBot.md)  
**Dev ref:** [`20260405_Sprint002_DEV_ShiftNotificationBot.md`](20260405_Sprint002_DEV_ShiftNotificationBot.md)

---

## Test Scope

| Module                    | Unit tests | Integration | UAT |
|---------------------------|------------|-------------|-----|
| `config.py`               | ✅          | —           | ✅   |
| `cli.py`                  | ✅          | —           | —   |
| `db.py`                   | ✅          | —           | ✅   |
| `schedule_parser.py`      | ✅          | —           | ✅   |
| `shift_logic.py`          | ✅          | —           | —   |
| `main.py` health mode     | —          | ✅           | ✅   |
| `main.py` dry-run mode    | —          | ✅           | ✅   |
| `main.py` reload-schedule | —          | ✅           | ✅   |

All unit tests run with **no network, no real `.env`, no real XLSX** — fixtures only.  
Integration tests use `tests/fixtures/sample_schedule.xlsx` and a temp DB file.

---

## Unit Tests

### TC-CONFIG-01 — All variables present
**Input:** `.env` with all 5 required variables set  
**Expected:** `load_config()` returns dict with all 5 keys, no exception, no exit

### TC-CONFIG-02 — One variable missing
**Input:** `.env` missing `TELEGRAM_BOT_TOKEN`  
**Expected:** stdout contains `[CONFIG] ❌ missing required variable: TELEGRAM_BOT_TOKEN`, `SystemExit(1)` raised

### TC-CONFIG-03 — Multiple variables missing
**Input:** `.env` missing `DB_PATH` and `LOG_DIR`  
**Expected:** both missing vars reported, `SystemExit(1)` raised

---

### TC-CLI-01 — No flags → health mode
**Input:** `sys.argv = ['main.py']`  
**Expected:** `RunMode(mode='health', employee=None, force=False, dry_run=False)`

### TC-CLI-02 — `--production`
**Expected:** `RunMode(mode='production', ...)`

### TC-CLI-03 — `--dry-run`
**Expected:** `RunMode(mode='dry_run', dry_run=True, ...)`

### TC-CLI-04 — `--production --employee "Alice Kovalenko"`
**Expected:** `RunMode(mode='production', employee='Alice Kovalenko', ...)`

### TC-CLI-05 — `--production --force`
**Expected:** `RunMode(mode='production', force=True, ...)`

### TC-CLI-06 — `--reload-schedule`
**Expected:** `RunMode(mode='reload_schedule', ...)`

### TC-CLI-07 — `--reload-schedule --dry-run`
**Expected:** `RunMode(mode='reload_schedule', dry_run=True, ...)`

### TC-CLI-08 — `--force` without `--production` (invalid)
**Expected:** `SystemExit(1)`, usage message printed

### TC-CLI-09 — `--employee` without `--production` (invalid)
**Expected:** `SystemExit(1)`, usage message printed

### TC-CLI-10 — Unknown flag
**Input:** `--send`  
**Expected:** `SystemExit(1)`, usage message printed

---

### TC-DB-01 — DB created on first run
**Input:** non-existent path  
**Expected:** file created, both tables exist, WAL mode enabled

### TC-DB-02 — Schema idempotent
**Input:** call `init_db()` twice on same path  
**Expected:** no error, tables still exist with correct schema

### TC-DB-03 — `was_notified()` → False when no record
**Input:** empty DB, any employee + date  
**Expected:** `False`

### TC-DB-04 — `was_notified()` → True after successful record
**Input:** `record_notification(..., status='ok')` then `was_notified()`  
**Expected:** `True`

### TC-DB-05 — `was_notified()` → False after failed record
**Input:** `record_notification(..., status='fail')` then `was_notified()`  
**Expected:** `False` — failed sends are retryable

### TC-DB-06 — `clear_notifications_for_dates()` clears correct dates only
**Input:** records for 2026-04-01 and 2026-04-02; clear only 2026-04-01  
**Expected:** 2026-04-01 record deleted, 2026-04-02 record intact; returns count=1

### TC-DB-07 — `get_pending_count()` correct
**Input:** 5 shifts, 2 already notified  
**Expected:** returns 3

---

### TC-PARSER-01 — Valid XLSX parsed correctly
**Input:** `tests/fixtures/sample_schedule.xlsx`  
**Expected:** 5 `Shift` objects returned; dates in ISO format; all fields populated

### TC-PARSER-02 — Missing column in Sheet 1
**Input:** XLSX with `duty_type` column removed  
**Expected:** `SystemExit(1)`, log contains column name `duty_type`

### TC-PARSER-03 — Employee in Sheet 1 not in Sheet 2 registry
**Input:** Sheet 1 row with `employee_name = "Unknown Person"`  
**Expected:** warning logged with employee name, row skipped, no crash, remaining rows parsed

### TC-PARSER-04 — Empty `contact_id` in registry
**Input:** registry row with blank `contact_id`  
**Expected:** warning logged, employee skipped, no crash

### TC-PARSER-05 — Mtime guard fires
**Input:** XLSX file touched (mtime = now)  
**Expected:** `RuntimeError` raised with path and mtime in message

### TC-PARSER-06 — Mtime guard passes
**Input:** XLSX file mtime = 90 seconds ago  
**Expected:** no error, parsing proceeds normally

### TC-PARSER-07 — Date conversion
**Input:** Sheet 1 date value `01-04-2026`  
**Expected:** `Shift.shift_date == '2026-04-01'`

---

### TC-LOGIC-01 — Prev/next found for middle shift
**Input:** 5 shifts from fixture (sorted), evaluate Carol Melnyk 2026-04-01 Night  
**Expected:** `prev_colleague = Alice Kovalenko (Night, 2026-03-31)`, `next_colleague = Alice Kovalenko (Day, 2026-04-02)`

### TC-LOGIC-02 — No prev for first shift
**Input:** first shift in sorted list for a given role  
**Expected:** `prev_colleague = None`

### TC-LOGIC-03 — No next for last shift
**Input:** last shift in sorted list for a given role  
**Expected:** `next_colleague = None`

### TC-LOGIC-04 — Role isolation
**Input:** mix of Nurse and Doctor shifts on same date  
**Expected:** Nurse's prev/next are Nurses only; Doctor's prev/next are Doctors only

### TC-LOGIC-05 — Pure function — no side effects
**Input:** call `compute_contexts()` twice with same list  
**Expected:** same result both times; input list unchanged

---

## Integration Tests

### TC-INT-01 — Health check — all green
**Setup:** valid `.env`, valid fixture XLSX, fresh temp DB  
**Run:** `python main.py`  
**Expected output contains:**
```
[CONFIG]  ✅ all variables loaded
[DB]      ✅ shift_bot.db reachable, schema valid
[XLSX]    ✅ schedule.xlsx found — 4 employees, 3 shift dates
[PENDING] 4 employees pending notification
```
**Expected exit code:** 0

### TC-INT-02 — Health check — config failure
**Setup:** `.env` missing `LOG_DIR`  
**Run:** `python main.py`  
**Expected:** `[CONFIG] ❌` in output, exit code 1

### TC-INT-03 — Health check — XLSX not found
**Setup:** `XLSX_PATH` points to non-existent file  
**Run:** `python main.py`  
**Expected:** `[XLSX] ❌` in output with path, exit code 1

### TC-INT-04 — Dry-run output
**Setup:** valid env, fixture XLSX, fresh DB  
**Run:** `python main.py --dry-run`  
**Expected:** one preview block per employee showing duty, date, prev, next  
**Expected:** DB has zero rows after run  
**Expected:** exit code 0

### TC-INT-05 — Reload schedule
**Setup:** DB has 3 notification records for 2026-04-01, 2026-04-02; run `--reload-schedule`  
**Expected:** records for both dates deleted; log confirms count; exit code 0

### TC-INT-06 — Reload schedule dry-run
**Setup:** same as above  
**Run:** `python main.py --reload-schedule --dry-run`  
**Expected:** log shows what would be deleted; DB unchanged after run

---

## UAT Checklist — Owner Executes

> Prerequisites: Python 3.11.14 venv set up locally. `.env` file configured with valid paths.  
> No Telegram token required — use the placeholder from `.env.example`.

| #   | Action                                                         | Expected result                                                           | Pass/Fail | Notes |
|-----|----------------------------------------------------------------|---------------------------------------------------------------------------|-----------|-------|
| U01 | Run `python main.py` with valid `.env` and fixture XLSX        | Health check prints ✅ for CONFIG, DB, XLSX; exit 0                        |           |       |
| U02 | Run `python main.py` after deleting one env variable           | ❌ line with variable name printed; exit 1                                 |           |       |
| U03 | Run `python main.py` with `XLSX_PATH` pointing to missing file | ❌ XLSX line with path printed; exit 1                                     |           |       |
| U04 | Run `python main.py --dry-run`                                 | Preview printed for each employee with duty, date, prev shift, next shift |           |       |
| U05 | Verify DB has zero rows after `--dry-run`                      | `shift_bot.db` notifications table is empty                               |           |       |
| U06 | Run `python main.py --reload-schedule`                         | Log confirms dates cleared; exit 0                                        |           |       |
| U07 | Run `python main.py --reload-schedule --dry-run`               | Log shows what would be cleared; DB unchanged                             |           |       |
| U08 | Verify log file written to `LOG_DIR` after each run            | File `shift_bot_YYYYMMDD_HHMMSS.log` exists                               |           |       |
| U09 | Run `python main.py --force` (without `--production`)          | Error message printed, exit 1                                             |           |       |
| U10 | Review dry-run output for boundary row (March 31)              | Alice Kovalenko April 1 shows prev = Alice Kovalenko March 31 Night       |           |       |

---

## Sprint 002 Sign-off

| Role | Name | Date | Status |
|---|---|---|---|
| Architect | AI | 2026-04-05 | ✅ |
| Developer | AI | 2026-04-05 | ✅ |
| QA Engineer | AI | 2026-04-05 | ✅ |
| **Owner** | | | ⏳ **UAT pending** |

> Sprint closes when Owner marks all UAT items Pass and signs off above.
