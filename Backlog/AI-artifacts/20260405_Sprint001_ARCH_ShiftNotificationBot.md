# Technical Blueprint — Shift Schedule Notification Bot
**Sprint:** 001  
**Role:** Architect  
**Date:** 2026-04-05  
**Status:** ✅ APPROVED — P1 Telegram, P2 Viber deferred, Python 3.11.14 confirmed


### Sprint status
Status [DONE]
Assigned to [OWNER]

Note the flow: Owner <-> Architect <-> Developer <-> QA -> Owner.

## Diagrams

| Diagram    | File                                             | View                                                                            |
|------------|--------------------------------------------------|---------------------------------------------------------------------------------|
| Deployment | [`Backlog/deployment.puml`](../deployment.puml)  | Infrastructure: hosting, cron, env, APIs, actors                                |
| Component  | [`Backlog/component.puml`](../component.puml)    | Internal: Adapter pattern, module boundaries, boot sequence, dependency locality |

**Sprint Plan:** [`20260405_SprintPlan_ShiftNotificationBot.md`](20260405_SprintPlan_ShiftNotificationBot.md) — sprint register, SDLC stages, UAT gates, handoff protocol

---

## User Task

The system reads an XLSX schedule file and sends each employee a personal message via their preferred messenger containing:

> **P1 (PoC):** Telegram only.  
> **P2:** Viber — deferred until Telegram is live and Viber proactive messaging is verified.

- Their duty type, date, and shift time
- Name and role of the previous shift colleague
- Name and role of the next shift colleague

Triggered by a cPanel cron job on the Schedule Manager's defined schedule.

---

## Tech Stack

| Layer                | Technology                                              |
|----------------------|---------------------------------------------------------|
| Language             | Python 3.11.14 (confirmed available in cPanel Python Selector) |
| XLSX parsing         | `openpyxl`                                             |
| Messenger — P1       | Telegram via `requests` (direct REST)                  |
| Messenger — P2       | Viber via `requests` (direct REST) — deferred, see Q6  |
| Config / secrets     | `python-dotenv`                                        |
| Database             | SQLite via `sqlite3` (Python stdlib — no install)      |
| Dependency isolation | `venv` in home directory                               |
| Trigger              | cPanel cron job                                        |
| Logging              | Flat file → `~/logs/` with timestamps (cPanel mandated)|
| Hosting              | Namecheap Shared Hosting (cPanel)                      |

---

## Feasibility Check

| Item                  | Assessment                                                              |
|-----------------------|-------------------------------------------------------------------------|
| XLSX parsing          | ✅ `openpyxl` — stable, no external service required                    |
| Telegram Bot API      | ✅ P1 — REST `sendMessage`, chat_id sufficient, no webhook required    |
| Viber Bot API         | ⏸ P2 — deferred pending Developer verification of proactive messaging  |
| Messenger credentials | ✅ Stored in environment variables — no secrets in code                 |
| XLSX file access      | ✅ Absolute path via env variable (cPanel path context requirement)     |
| Cron execution        | ✅ cPanel cron supports Python venv scripts                             |
| Volume                | ✅ PoC — small staff count, no rate-limit concerns                      |
| Hosting constraints   | ✅ One-shot script design complies with Namecheap no-daemon rule        |
| SQLite                | ✅ `sqlite3` is Python stdlib — no install, no server, `.db` file only  |

---

## Dependency Mapping

### Runtime
| Library         | Purpose                                                                   |
|-----------------|---------------------------------------------------------------------------|
| `openpyxl`      | XLSX parsing                                                              |
| `requests`      | Telegram + Viber REST API calls                                           |
| `python-dotenv` | Load environment variables from `.env`                                    |
| `sqlite3`       | Notification audit log and receipts (Python stdlib — no install required) |

> **Why `requests` instead of messenger SDKs:**  
> Namecheap Shared Hosting kills long-running processes. `python-telegram-bot` (polling)  
> and `viberbot` (webhook server) both require persistent processes. For send-only PoC,  
> direct REST calls via `requests` are sufficient and fully compliant with cron-first hosting.

### Architecture Pattern: Adapter

> **Diagram:** [`Backlog/component.puml`](../component.puml) — visual representation of the Adapter pattern, module boundaries, boot sequence, and dependency locality rule.

```
main.py                        ← entry point; orchestrates the flow
cli.py                         ← argument parsing; defines run mode from flags
config.py                      ← loads and validates env variables at startup
schedule_parser.py             ← reads XLSX, returns typed data model
shift_logic.py                 ← pure functions: find prev/next shift per employee
db.py                          ← SQLite init, schema creation, read/write helpers
messenger/
    gateway.py                 ← abstract interface MessengerGateway
    telegram_adapter.py        ← Telegram REST implementation (uses requests) — P1
    viber_adapter.py           ← Viber REST implementation (uses requests)   — P2 (deferred)
logs/                          ← runtime log output (~/logs/ on hosting)
shift_bot.db                   ← SQLite database file (gitignored, absolute path via env)
.env.example                   ← placeholder values only — committed to git
.env                           ← real secrets — gitignored, never committed
requirements.txt               ← pinned versions — committed to git
```

**Shift calculation logic** — what belongs in `shift_logic.py`:
- Accepts the full list of shifts already parsed from XLSX (no file I/O here)
- Sorts shifts by date/time
- For each employee's shift, finds the adjacent shifts by position in the sorted list
- Returns previous colleague (name + role) and next colleague (name + role)
- Pure functions only — no XLSX access, no network calls, no logging
- Fully unit-testable with a hardcoded list of shifts, no external dependencies

**Dependency locality rule:** `telegram_adapter.py` and `viber_adapter.py` are the only files
allowed to call messenger REST endpoints. No direct `requests` calls to messenger APIs may
appear in `shift_logic.py`, `schedule_parser.py`, or `main.py`.

---

## Constraint Logic — What This System Will NOT Do

- No real-time shift swaps
- No payroll integration
- No mobile app or web UI
- No two-way conversation handling beyond optional receipt reply (PoC scope)
- No automatic scheduling — cron schedule is set once by IT Owner, not by the script
- No modification of the XLSX file — read-only
- No server-based database — SQLite only (single `.db` file, stdlib, no server process)
- No persistent process — script runs, completes, and exits on every cron invocation

---

## Developer Directives

### CLI Interface

| Command | Behaviour |
|---|---|
| `python main.py` | **Health check** — config, DB, XLSX, API connectivity, last run, pending count. No send, no DB write. Safe to run anytime. |
| `python main.py --dry-run` | Preview what would be sent. No send, no DB write |
| `python main.py --production` | Real run — send to unnotified employees, write to DB |
| `python main.py --production --employee "Name"` | Call feature — force send to one person, bypass dedup |
| `python main.py --production --force` | Re-send everyone, bypass dedup |
| `python main.py --reload-schedule` | Validate XLSX, clear dedup for dates in new file. No send |
| `python main.py --reload-schedule --dry-run` | Validate XLSX only, show what would reset. No DB change |

**Health check output format:**
```
[CONFIG]    ✅ all variables loaded
[DB]        ✅ shift_bot.db reachable, schema valid
[XLSX]      ✅ schedule.xlsx found — 12 employees, 3 shift dates
[TELEGRAM]  ✅ bot reachable (token valid)
[VIBER]     ✅ bot reachable (token valid)
[LAST RUN]  2026-04-04 09:00 — 12 sent, 0 failed
[PENDING]   3 employees not yet notified for 2026-04-06
```
Any failed check prints ❌ with the reason. Exit code 1 if any check fails.

**Safety rule:** No message is ever sent without `--production` flag present.  
Default behaviour (`python main.py`) is always health check — never sends.

**Cron line must explicitly declare intent:**
```bash
/home/<user>/venv/bin/python /home/<user>/<script>/main.py --production
```

**Idempotency rule:** Before sending to any employee, `db.py` checks `notifications` for `(employee_name, shift_date)`. If a record exists with `status = 'ok'` — skip. Bypassed only by `--force` or `--employee`.

**`--reload-schedule` behaviour:** Parses XLSX, validates schema, then deletes `notifications` records whose `shift_date` appears in the new file. Does not delete records for past dates not in the file. Cron will re-send on next `--production` run.

---

### Startup vs. User Action
- `config.py` loads and validates all environment variables at **app startup**. If any required variable is missing: **print a clear error message, write to log, and exit with code 1** — do not proceed with a broken config.
- XLSX file is read **on each run** (not cached) — Schedule Manager may update it between runs.
- `requests.Session` objects for each messenger are initialised **once at startup** after config validation.

### Hosting Compliance (Namecheap Shared — MANDATORY)
> **Diagram:** [`Backlog/deployment.puml`](../deployment.puml) — infrastructure view of hosting boundary, cron trigger, file system artifacts, and external API connections.

- All file paths in config and logging must be **absolute paths** — cron loses PATH context.
- Script must be invoked via venv Python: `/home/<user>/venv/bin/python /home/<user>/<script>/main.py`
- All output (stdout + stderr) must be written to `~/logs/shift_bot_YYYYMMDD_HHMMSS.log`.
- No global pip installs — all dependencies installed inside venv only.
- No daemons, no background threads, no `while True` loops — ever.

### Initialisation Failures
| Failure                               | Behaviour                                               |
|---------------------------------------|---------------------------------------------------------|
| Missing env variable                  | Log missing variable name, exit with code 1             |
| DB file path not set or unwritable    | Log absolute path, exit with code 1                     |
| XLSX file not found                   | Log absolute file path, exit with code 1                |
| XLSX schema mismatch (missing column) | Log column name, exit with code 1                       |
| XLSX modified within last 60 seconds  | Log warning "upload in progress", exit with code 1 — cron retries next run |
| Messenger API auth failure            | Log adapter name and HTTP status, exit with code 1      |
| Single message send failure           | Log employee name and error, continue to next employee  |

### Sequencing Rules
> **Diagram:** [`Backlog/component.puml`](../component.puml) — boot sequence ①–⑥ visualised on orchestration arrows from `main.py`.

1. Load config → 2. Init DB → 3. Init messenger sessions → 4. Parse XLSX → 5. Run shift logic → 6. Dispatch messages → 7. Write summary log
- Steps 1–4 must all succeed before any message is sent.
- Step 5 must complete for all employees before Step 6 begins.
- No partial sends where half the staff receive messages and half do not due to a logic error.

### DO / DO NOT
- **DO** use `MessengerGateway` interface in `main.py` — never call adapters directly in main
- **DO NOT** put shift calculation logic in `main.py` — it belongs in `shift_logic.py`
- **DO NOT** send any message without `--production` flag — health check and dry-run must never trigger sends
- **DO** implement all argument parsing in `cli.py` — `main.py` receives a mode object, not raw `sys.argv`
- **DO** design `shift_logic.py` to filter prev/next by `(role, location)` even though location is a single constant for PoC — multi-ward support is planned for v2
- **DO NOT** hardcode any token, path, phone number, or chat ID in any source file
- **DO NOT** log messenger tokens or employee contact details to log files or stdout
- **DO** use absolute paths everywhere — relative paths will silently fail under cron
- **DO** raise a [RED FLAG] if any library requires a persistent process or webhook endpoint
- **DO** enable WAL journal mode in `db.py` on every connection open: `PRAGMA journal_mode=WAL`
- **DO** check XLSX mtime in `schedule_parser.py` — abort if file modified within last 60 seconds
- **DO** return `"-"` from `shift_logic.py` when no previous or next shift exists — this is valid, not an error
- **DO** include the last shift of the previous period in the XLSX as a boundary reference row (Schedule Manager responsibility — document in runbook)
- **DO** verify Viber proactive messaging in current API docs before coding `viber_adapter.py` — [RED FLAG] if webhook registration is mandatory at runtime

---

## Success Metrics — Definition of Done

- [ ] All employees in the XLSX receive a correctly formatted message in their chosen messenger
- [ ] Previous and next shift fields are accurate for every employee
- [ ] Missing or invalid XLSX data produces a clear error in the log, not a crash or silent skip
- [ ] No credentials or PII appear in any source file or log output
- [ ] All unit tests for `shift_logic.py` pass (pure logic, no network calls)
- [ ] Script exits with code 0 on success, code 1 on any fatal error
- [ ] Log file written to `~/logs/` on every run (success and failure)
- [ ] SQLite DB created automatically on first run; schema verified on every run
- [ ] Every send attempt (success or failure) recorded in `notifications` table
- [ ] `python main.py` returns health check with ✅/❌ per component; exit code 1 if any check fails
- [ ] `python main.py --dry-run` prints preview with zero sends and zero DB writes
- [ ] No message sent without `--production` flag — verified by running without it
- [ ] `--reload-schedule` clears only dedup records for dates present in the new XLSX
- [ ] Manual end-to-end test: cron invocation (`--production`) with sample XLSX, verify messages received and DB populated

---

## Security Compliance

Per `AI-assistance/Quality/Security.md`:
- Messenger tokens stored in environment variables only — never in code or XLSX
- `.env` is in `.gitignore`; `.env.example` with placeholder values is committed
- XLSX path provided via environment variable — no hardcoded paths
- Employee contact data (Chat ID / Phone) lives in XLSX only — not duplicated in code or logs
- No PII in any sprint artifact, directive, or example value
- `~/logs/` directory must not be publicly web-accessible — block via `.htaccess` if under `public_html`
- `shift_bot.db` must not be publicly web-accessible — store outside `public_html` or block via `.htaccess`
- `shift_bot.db` path provided via environment variable — no hardcoded paths

---

## Data Storage

| Data                                                     | Storage                                | Owner            | Notes                                                           |
|----------------------------------------------------------|----------------------------------------|------------------|-----------------------------------------------------------------|
| Schedule (dates, shifts, duties)                         | `schedule.xlsx` Sheet 1                | Schedule Manager | Read-only by bot                                                |
| Employee registry (name, role, messenger, chat ID/phone) | `schedule.xlsx` Sheet 2                | Schedule Manager | Read-only by bot                                                |
| Bot tokens, file paths, DB path                          | `.env`                                 | IT Owner         | Never committed to git                                          |
| Notification audit (who, when, status)                   | `shift_bot.db` → `notifications` table | system           | Written on every send attempt                                   |
| Receipt confirmations                                    | `shift_bot.db` → `receipts` table      | system           | Written on staff reply (v2 feature, table created from day one) |
| Runtime errors and run summary                           | `~/logs/shift_bot_YYYYMMDD_HHMMSS.log` | system           | Flat file, human-readable                                       |

### SQLite Schema

```sql
-- Created automatically by db.py on first run
CREATE TABLE IF NOT EXISTS notifications (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name TEXT    NOT NULL,
    shift_date    TEXT    NOT NULL,  -- ISO 8601 date — deduplication key
    messenger     TEXT    NOT NULL,  -- 'telegram' | 'viber'
    sent_at       TEXT    NOT NULL,  -- ISO 8601 datetime
    status        TEXT    NOT NULL,  -- 'ok' | 'fail'
    error         TEXT               -- NULL on success
);
-- Deduplication: UNIQUE (employee_name, shift_date) enforced in db.py logic
-- --reload-schedule clears records for dates present in the new XLSX
-- --production --force bypasses the check entirely

CREATE TABLE IF NOT EXISTS receipts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name TEXT    NOT NULL,
    replied_at    TEXT    NOT NULL,  -- ISO 8601
    message       TEXT               -- raw reply text
);
```

> `db.py` is the only module allowed to read from or write to `shift_bot.db`.  
> No direct SQL may appear in `main.py`, adapters, or any other module.

---

## Roadmap

Each deliverable is independently testable before the next phase begins.  
Phases 1–2 require no hosting access and no messenger tokens. Phase 3 runs fully local end-to-end. Phase 4 is the production deploy.

---

### Phase 1 — Foundation
*Goal: project runs, config validates, data parses, logic computes — no network calls needed.*

**Deliverable 1.1 — Project scaffold & config**
- `requirements.txt` with pinned versions
- `.env.example` with all required variable names, no real values
- `config.py` — loads and validates all env variables at startup
- **Test:** run with one variable missing → verify `exit(1)` and clear error message in log

**Deliverable 1.2 — XLSX Parser**
- `schedule_parser.py` — reads `schedule.xlsx`, returns typed list of Shift objects
- **Test:** unit test with sample XLSX → verify correct data model; test with missing column → verify `exit(1)` with column name in log

**Deliverable 1.3 — Shift Logic**
- `shift_logic.py` — pure functions: sort shifts, find prev/next by `(role, location)`
- **Test:** unit tests with hardcoded shift list — cover Day, Night, 24h duty types; verify first shift has no prev, last shift has no next; zero external dependencies required to run tests

**Deliverable 1.4 — Database layer**
- `db.py` — creates `shift_bot.db` on first run, applies schema (`notifications`, `receipts`), exposes read/write helpers
- **Test:** run against a temp path → verify both tables created; insert a notification row → verify it is returned by query; run twice → verify idempotent (`IF NOT EXISTS`); verify dedup check correctly skips `(employee_name, shift_date)` already marked `ok`

**Deliverable 1.5 — CLI layer**
- `cli.py` — parses `sys.argv`, returns a mode object to `main.py`; defines all valid flags and their combinations
- `python main.py` → health check mode (no send, no DB write)
- `python main.py --production` → real run mode
- `python main.py --dry-run` → preview mode
- `python main.py --reload-schedule` → reload mode
- **Test:** invoke with each flag combination → verify correct mode object returned; verify invalid flag combinations exit with code 1 and usage message

---

### Phase 2 — Messenger Adapter (P1: Telegram)
*Goal: real Telegram messages delivered. Requires a valid bot token and a personal Telegram test account.*

**Deliverable 2.1 — Gateway interface and Telegram adapter**
- `messenger/gateway.py` — abstract `MessengerGateway` interface
- `messenger/telegram_adapter.py` — Telegram REST `sendMessage`
- `messenger/viber_adapter.py` — scaffold only (empty implementation, raises `NotImplementedError`) — P2
- **Test:** send a test message to a personal Telegram chat → verify delivery; test with invalid token → verify `exit(1)` with adapter name and HTTP status in log

---

### Phase 3 — Integration (local end-to-end)
*Goal: full script runs locally against a sample XLSX, all employees notified, log written.*

**Deliverable 3.1 — Orchestrator**
- `main.py` — full boot sequence ①–⑦ wired via `MessengerGateway` and `db.py`
- **Test:** local run with sample XLSX (minimum 3 employees, mixed messenger types) → verify each employee receives a correctly formatted message; verify `notifications` table populated with correct status per employee; verify log written to `~/logs/`; verify `exit(0)`; verify `exit(1)` on XLSX not found

---

### Phase 4 — Production Deploy (Namecheap cPanel)
*Goal: script runs on hosting, triggered by cron, zero manual intervention.*

**Deliverable 4.1 — Hosting setup**
- venv created, dependencies installed (`pip install -r requirements.txt` inside venv)
- `.env` configured on server with real tokens and absolute paths
- cron job configured by IT Owner: `/home/<user>/venv/bin/python /home/<user>/<script>/main.py`
- **Test:** trigger cron manually from cPanel → verify messages received; verify log file created in `~/logs/`; verify no tokens or PII in log output

**Deliverable 4.2 — Hardening**
- `~/logs/` blocked from public web access (`.htaccess` if logs are under `public_html`)
- `shift_bot.db` blocked from public web access
- **Test:** attempt to access log and DB file URLs in browser → verify `403 Forbidden`

**Deliverable 4.3 — Hardening** *(P1 complete)*
- `shift_bot.db` blocked from public web access
- Confirm cron schedule is stable, logs rotating correctly
- **Test:** full end-to-end health check → all ✅

---

### P2 — Viber Messenger (deferred)
*Pause here. Do not begin until Telegram P1 is live and stable in production.*

**Deliverable P2.1 — Viber API verification**
- Developer reviews current Viber Bot API docs for proactive messaging capability
- Reports findings: can we send without prior staff contact? Is webhook registration required?
- **Gate:** Architect reviews findings and approves implementation approach before any code is written

**Deliverable P2.2 — Viber staff onboarding**
- Each staff member on Viber sends "Hello" to the bot once — IT Owner records Viber ID in XLSX
- If webhook registration required: run one-time registration script
- **Test:** IT Owner can send a manual test message to each Viber staff member

**Deliverable P2.3 — Viber adapter**
- `messenger/viber_adapter.py` — full Viber REST `send_message` implementation (replaces scaffold)
- **Test:** end-to-end run with mixed Telegram + Viber staff → verify both messengers deliver correctly

---

### v2 — Multi-Ward (future, outside PoC scope)

- Add `location` column to XLSX schema
- `shift_logic.py` already filters by `(role, location)` — extension, not a rewrite
- Deploy to additional wards or locations with separate `.env` per instance

---

## Discussion

> Questions below must be answered by **Owner** before Developer sprint begins.  
> Record answers here in this document.

1. **Q1 — Trigger mechanism** *(assigned to: Owner)*  
Resolved: cron job on Namecheap cPanel. IT Owner sets the cron schedule.  
**Answer:** ✅ cPanel cron job

2. **Q2 — Shift clock times** *(assigned to: Owner)*  
What are the actual clock times for each duty type?  
**Answer Owner -> Architect:** ✅ Shift times are configurable settings per deployment — not architecture-level constants. Different hospitals, wards, or teams may use different hours. Times are stored in a dedicated config/settings file and applied system-wide. `shift_logic.py` operates on duty type and position in the sorted shift list, not on hardcoded clock values.

3. **Q3 — Location scope** *(assigned to: Owner)*  
The PRL mentions finding prev/next shift by "same location, same role" — but the Inputs section has no location column.  
Is this a single-location operation for the PoC, or must location be added to the XLSX schema?  
**Answer Owner -> Architect:** ✅ Single location for PoC. Multi-ward (multi-location) support planned for a future version. No `location` column in XLSX yet — but `shift_logic.py` must filter prev/next by `(role, location)` from the start so adding location in v2 is an extension, not a rewrite.

4. **Q4 — Python version in cPanel** *(assigned to: Owner)*  
Check Python Selector in cPanel and confirm which Python version (3.x) is available.  
Run in cPanel terminal: `python3 --version`  
**Answer Owner -> Architect:** ✅ Python 3.6.15 initially noted. Superseded by Q5 — see below.

5. **Q5 — Python version CRITICAL** *(Consultant → Architect → Owner)*  
Python 3.6.15 reached End of Life in December 2021. No security patches have been issued since. Running production code on an EOL runtime is unacceptable.  
**Answer Owner -> Architect:** ✅ Python **3.11.14** confirmed available and selected in cPanel Python Selector.  
**Impact:** Tech Stack updated to 3.11.14. No Python 3.6 coding restrictions. Developer may use all 3.11 features.

6. **Q6 — Viber REST API proactive messaging** *(Consultant → Architect)*  
[RED FLAG] The Viber REST API requires a webhook URL to be registered before proactive messages can be sent. Unlike Telegram (chat_id is sufficient), Viber may require staff to initiate contact first and a one-time dummy webhook registration to unlock the token.  
**Architect decision:** Viber deferred to **P2**. Telegram is P1 (PoC). Implementation will pause at the Viber stage until Developer verifies proactive messaging capability against current Viber API docs.  
**P2 plan:**  
  - Developer reviews Viber API docs and reports findings before `viber_adapter.py` is coded  
  - Staff onboarding step: each Viber staff member sends "Hello" to bot once; IT Owner records Viber ID in XLSX  
  - One-time webhook registration if required — deploy-time task, not runtime  
  - Deliverable 4.3 (Viber onboarding) remains in Roadmap under P2 phase  
**Status:** ✅ scoped to P2 — no action needed until Telegram P1 is live.

7. **Q7 — SQLite concurrency on shared file systems** *(Consultant → Architect)*  
SQLite can suffer from locking or corruption on NFS-backed shared hosting if multiple write processes access the `.db` file simultaneously.  
**Architect assessment:** Low risk for PoC — single cron job, no concurrent writes expected. Mitigation applied: `db.py` must enable WAL journal mode (`PRAGMA journal_mode=WAL`) on every connection open. This allows concurrent reads without blocking.  
**Becomes critical when:** multiple cron instances run simultaneously (misconfigured cron), or `--employee` is triggered manually while cron is mid-run. Addressed in v2 multi-ward design.  
**Status:** ✅ documented, WAL mode added to `db.py` directive.

8. **Q8 — XLSX file lock race condition** *(Consultant → Architect)*  
If the cron job fires at the exact moment the Schedule Manager is uploading or saving `schedule.xlsx`, the script may read a partial or corrupt file.  
**Architect decision:** `schedule_parser.py` must check file modification time before parsing. If the file was modified within the last 60 seconds, abort with a clear log message and exit code 1 (not a fatal crash — cron will retry on next scheduled run).  
```python
import os, time
if time.time() - os.path.getmtime(xlsx_path) < 60:
    raise RuntimeError("XLSX modified within 60s — possible upload in progress. Skipping run.")
```  
**Status:** ✅ added to `schedule_parser.py` directive and Initialisation Failures table.

9. **Q9 — Prev/next shift boundary edge case** *(Consultant → Architect)*  
When running for the first shift of a new period (e.g., April 1), there is no previous shift in the XLSX — it belongs to the prior period (e.g., March 31).  
**Architect decision:**  
  - `shift_logic.py` returns `"-"` (dash) when no previous or next shift exists. This is valid output, not an error.  
  - **Data requirement for Schedule Manager:** the XLSX for each new period must include the last shift of the previous period as a reference row. E.g., for an April schedule, include March 31 last shift. This row is used only for boundary calculation — it will not generate a notification (shift_date is in the past, dedup or date-filter will skip it).  
  - This requirement must be documented in the XLSX template and admin runbook.  
**Status:** ✅ documented. XLSX template note and `shift_logic.py` boundary behaviour added to Developer Directives.


5. Q5 Consultant -> Architect.  Python 3.6.15 is Dangerously Old (CRITICAL)
Can we select 3.10.x or 3.11.x (do not leave it on 3.6.15).

6. Viber REST API Limitation
   The Issue: The Viber REST API requires a webhook URL to be registered before you can send proactive messages, even if you are just using REST calls. Unlike Telegram, where you just need the chat_id, Viber often requires users to initiate contact with the bot first, and the bot responds.
   The Fix: Have the developer double-check the Viber API documentation for "proactive messaging". You may need a one-time script to register a dummy webhook just to unlock the token, and you must have a clear onboarding step where staff send a "Hello" to the Viber bot to get their chat_id.

7. SQLite Concurrency on Shared File Systems
   SQLite can suffer from database locking or corruption on NFS if multiple writes happen simultaneously.
   Record this risk and remind when it can become critical.

8. The "File Lock" Problem with XLSX
   The Issue: The Schedule Manager updates schedule.xlsx. What happens if the cron job triggers at the exact moment the manager is uploading/saving the file? 
   The Fix: Add a simple file-check mechanism. The script should verify the file hasn't been modified in the last 60 seconds before parsing it.

   python
   import os, time
   if time.time() - os.path.getmtime('schedule.xlsx') < 60:
   exit("File currently being modified. Skipping run.")

9. "Next/Previous Shift" Edge Case

   The Issue: The logic sorts shifts by date/time to find the previous/next colleague. 
   The fix: If no value - "Previous shift: -" is valid, but XLS needs to have (filled by human) previous period last shift. E.g. March 31 for running April setup. 