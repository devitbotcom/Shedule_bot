# Sprint 004b — Architecture

**Sprint:** 004b  
**Role:** Architect  
**Date:** 2026-05-02  
**Status:** ⚠️ REVISED — post-UAT corrections applied 2026-05-03 (OQ-3 wrong, AD-S004b-001 table corrected)  
**Scope:** Production deploy to Namecheap cPanel shared hosting. Minimal code change: one new check in `main.py` (clock drift monitor).  
**Depends on:** S004 ✅ DONE  
**Blocks:** S005 (dedup key + --shift-type scoping)

---

## Sprint Goal

The bot runs automatically in production on Namecheap cPanel shared hosting. IT deploys once via `git clone`, configures three cPanel cron entries, and shift notifications fire at the correct local times without any manual trigger.

---

## Scope Boundaries

| In scope                                   | Out of scope                                               |
|--------------------------------------------|------------------------------------------------------------|
| git-based deploy to cPanel                 | Docker (not available on shared hosting)                   |
| `venv` setup on server                     | `gen_crontab.py` (Docker-only)                             |
| 3 cPanel cron entries (one per shift type) | Viber adapter (S007)                                       |
| README — Production Install section        | S005 features (scoped --reload-schedule, dedup key change) |
| Security hardening (`chmod`)               | CI/CD pipeline                                             |
| Log retention cron                         | Any messenger or business logic changes                    |
| Clock drift monitor (AD-S004b-008)         | Viber adapter (S007)                                       |

**One Python change only:** `_check_clock_drift()` added to `main.py`. All other bot code unchanged. The bot already:
- Supports `--shift-type` flag (implemented S004)
- Uses `os.path.abspath` for all file operations
- Loads `.env` via `python-dotenv`
- Is a stateless one-shot CLI

---

## Key Architectural Decisions

### AD-S004b-001 — TZ prefix in every cPanel cron entry (resolves server-local/Kyiv date mismatch)

> ⚠️ **Post-UAT correction (2026-05-03):** OQ-3 was originally answered as UTC after a `export TZ='UTC'` shell override masked the real server timezone. The server is EDT (UTC-4). The cron table below has been corrected. The `TZ=Europe/Kyiv` decision is unchanged — it solves the same problem regardless of the server's base timezone.

**Problem:** The Namecheap server runs EDT (UTC-4). The bot uses `datetime.now()` to determine "today" when looking up shifts in the XLSX. Without a timezone override, `datetime.now()` returns the server's local date — which for shift types whose Kyiv notification time crosses midnight in server-local time (e.g., `other` at 01:25 Kyiv = 18:25 EDT the previous day), means the cron fires on calendar day D while the shift belongs to day D+1 in Kyiv time — causing the bot to find no shifts for that run.

**Decision:** Prefix every cPanel cron entry with `TZ=Europe/Kyiv`. This sets the timezone for the Python process before it starts, so `datetime.now()` returns Kyiv local time and date on all three cron entries.

Applied to all three entries for consistency — not only the midnight-crossing case.

**Cron entry format:**
```
TZ=Europe/Kyiv /home/<username>/shift_bot/venv/bin/python /home/<username>/shift_bot/main.py --production --shift-type <type>
```

**Server-local time conversion (server = EDT UTC-4, Kyiv = EEST UTC+3, offset = 7h):**

| Shift type | `shift_hours` (Kyiv EEST) | cPanel cron time (EDT) | Same calendar day?                                  |
|------------|--------------------------|------------------------|-----------------------------------------------------|
| labor      | 17:00                    | 10:00                  | ✅ Yes                                               |
| holiday    | 17:34                    | 10:34                  | ✅ Yes                                               |
| other      | 01:25                    | 18:25 (previous day)   | ⚠️ Crosses midnight — `TZ=` prefix is critical      |

**Formula:** cPanel cron time (EDT) = Kyiv time − 7h. If result is negative, subtract one calendar day.

⚠️ **DST note:** Both Kyiv and the server observe DST, but on different schedules. Current offset is 7h (EEST UTC+3 − EDT UTC-4). In winter: Kyiv → EET (UTC+2), server → EST (UTC-5), offset remains 7h. However, the transitions happen on different dates — verify the offset whenever either timezone changes clocks. IT must update all 3 cPanel cron entries when the offset changes.

---

### AD-S004b-002 — Deployment via `git pull`

`git` is available on the server (OQ-2 confirmed). Initial deploy is `git clone`; updates are `git pull`.

No build step. No Docker. After each pull, `pip install -r requirements.txt` inside the activated venv ensures dependencies are up to date.

**Git authentication:** IT configures SSH key access to the repository on the server manually before running `git clone`. README must include this as a prerequisite step.

---

### AD-S004b-003 — `venv` replaces container image

```bash
cd ~/shift_bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

All maintenance commands follow the pattern:
```bash
cd ~/shift_bot && source venv/bin/activate && python main.py <flags>
```

This replaces every `docker compose run --rm bot python main.py <flags>` from the local workflow.

---

### AD-S004b-004 — cPanel cron replaces supercronic + gen_crontab.py

`gen_crontab.py` runs at Docker container startup and generates the crontab automatically. This mechanism is not available on shared hosting.

**Decision:** IT configures 3 cron entries manually in the cPanel cron UI.

**Single source of truth gap:** When `shift_hours` in `schedule_mapping.json` is updated, IT must also update the 3 cPanel cron times manually (applying the server-local time offset — see AD-S004b-001 formula). This is a documented two-step — not a bug.

**README must make this explicit:**
> Whenever you change `shift_hours`, recalculate the server-local cron times using the offset formula in the cron table, and update all 3 cPanel cron entries.

---

### AD-S004b-005 — Absolute paths in `.env`

The cPanel cron runs with a minimal environment and a non-interactive shell. Relative paths will fail.

`.env` on the server must use absolute paths:
```
DB_PATH=/home/<username>/shift_bot/data/shift_bot.db
LOG_DIR=/home/<username>/shift_bot/data/logs
DATA_DIR=/home/<username>/shift_bot/data
```

The code already uses `os.path.abspath` — these `.env` values provide the roots.

---

### AD-S004b-006 — Security hardening

After deploy, IT runs once:
```bash
chmod 600 .env
chmod 700 data/logs
chmod 700 data
```

Then after the first `--production` run (which creates `shift_bot.db`):
```bash
chmod 600 data/shift_bot.db
```

Rationale: shared hosting means other processes on the same server may be able to read world-readable files. Tokens and DB must not be world-readable.

> **Architect note:** `shift_bot.db` does not exist at deploy time — it is created on first run. README must explicitly remind IT to apply `chmod 600` to the DB file after the first successful `--production` run.

---

### AD-S004b-007 — Log retention via cPanel cron

One additional cPanel cron entry (weekly, Sunday 03:00 EDT — server local time):
```
0 3 * * 0  find /home/<username>/shift_bot/data/logs -name "*.log" -mtime +30 -delete
```

Keeps logs for 30 days. Prevents unbounded disk growth on shared hosting.

---

### AD-S004b-008 — Clock drift monitor on every `--production` run

**Problem:** On a server with a manually maintained cron schedule, two silent failure modes exist: server clock drift (NTP issue) and DST misconfiguration (IT forgot to update cPanel cron entries after either Kyiv or server clocks changed). Both cause notifications to fire at the wrong real-world time with no error.

**Decision:** At the start of every `--production` run, query a public HTTP time API, compare the returned UTC time to `datetime.utcnow()`, and log the delta.

**Contract:**
- Non-blocking: if the API is unreachable, log a warning and continue — the send loop must not be prevented
- Threshold: delta > 300 seconds → `logger.warning(...)`; within threshold → `logger.info(...)`
- Log only (no Telegram alert) — this is an IT operational signal, visible in `data/logs/`
- Uses `requests` (already a project dependency) — no new library

**Location:** `_check_clock_drift()` private function in `main.py`, called at the top of `run_production()`.

```python
def _check_clock_drift() -> None:
    try:
        resp = requests.get("http://worldtimeapi.org/api/timezone/UTC", timeout=5)
        world_utc = datetime.fromisoformat(resp.json()["utc_datetime"])
        delta = abs((datetime.now(timezone.utc) - world_utc).total_seconds())
        if delta > 300:
            logging.warning("Clock drift: server deviates from world time by %.0fs — check server NTP or DST offset", delta)
        else:
            logging.info("Clock drift OK: %.0fs", delta)
    except Exception:
        logging.warning("Clock drift check skipped — time API unreachable")
```

---

### AD-S004b-009 — Show active shift_hours in health output (004b-1)

**Problem:** IT must open `schedule_mapping.json` to confirm which times the bot uses. A misconfigured `shift_hours` is invisible during health check.

**Decision:** Call the existing `_shift_hours(config)` inside `run_health()` and print a `[SCHEDULE]` line immediately after `[TIMEZONE]`.

**Output format:**
```
[SCHEDULE] shift_hours: labor=17:00  holiday=09:00  other=08:20
```

**Contract:**
- Uses existing `_shift_hours()` — no new function, no new dependency
- Non-blocking: if the call raises, print `[SCHEDULE] ❌ could not read schedule_mapping.json` and continue; do not set `all_ok = False` (schedule is not required for DB/Telegram health)
- Key order: `labor`, `holiday`, `other` — fixed display order regardless of JSON key order

---

### AD-S004b-010 — Show server local time and TZ offset in health output (004b-2)

**Problem:** With `TZ=Europe/Kyiv` active in the process, `datetime.now()` returns Kyiv time. IT cannot see the server's actual wall clock or verify the offset between bot TZ and server TZ — the two values needed to calculate cPanel cron times.

**Decision:** Use `subprocess.run(['bash', '-c', 'unset TZ && date'], ...)` to read the server's local time outside the `TZ` env var override. Calculate the offset by comparing the bot's UTC offset (from `datetime.now().astimezone().utcoffset()`) to the server's UTC offset (from `unset TZ && date +%z`).

Print two lines after `[SCHEDULE]`:
```
[ENV TIME]  Sun May  3 01:02:35 EDT 2026
[TZ OFFSET] bot leads server by 7h (Europe/Kyiv EEST UTC+3 vs server EDT UTC-4)
```

**Why subprocess:** `TZ` env var is inherited by all Python APIs (`time`, `datetime`, `tzlocal`). The only way to read the server's native timezone from within the same process is to spawn a child shell and unset the variable there. `subprocess` is stdlib — no new dependency.

**Contract:**
- Non-blocking: if subprocess fails, print `[ENV TIME]  ❌ could not read server local time` and skip `[TZ OFFSET]`; do not set `all_ok = False`
- Offset label: positive diff → "bot leads server by Xh"; negative → "server leads bot by Xh"; zero → "bot and server clocks match"
- Timeout: 3 seconds on the subprocess call

**Line order in health output:**
```
[CONFIG]
[TIMEZONE]   ← bot configured TZ + Kyiv datetime
[SCHEDULE]   ← shift_hours (AD-S004b-009)
[ENV TIME]   ← server local datetime (AD-S004b-010)
[TZ OFFSET]  ← derived offset (AD-S004b-010)
[DB]
[TELEGRAM]
[XLSX]
[LAST RUN]
[PENDING]
```

---

## Developer Deliverables

| #  | Deliverable                                     | Notes                                                                                                                                          |
|----|-------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| D1 | README — Production Install section             | Full step-by-step: git clone, venv, .env, cPanel cron setup, verify                                                                            |
| D2 | README — server-local cron conversion table     | Shows how to convert `shift_hours` to EDT cron times using offset formula; DST warning (corrected from UTC — UAT finding 004b-4)               |
| D3 | README — Production maintenance commands        | Replaces `docker compose run --rm bot` equivalents                                                                                             |
| D4 | README — Security hardening step                | chmod instructions, one-time after deploy                                                                                                      |
| D5 | README — Log retention cron entry               | Weekly find/delete command                                                                                                                     |
| D6 | `.env.example` — add absolute path placeholders | `DB_PATH`, `LOG_DIR`, `DATA_DIR` with `<username>` placeholder and note                                                                        |
| D7 | `main.py` — `_check_clock_drift()` function     | Called at start of `run_production()`; non-blocking; logs WARNING if delta > 5 min (AD-S004b-008)                                              |
| D8 | Unit tests for `_check_clock_drift()`           | Positive: delta < 300s → INFO logged. Negative: delta > 300s → WARNING logged. Negative: API unreachable → WARNING logged, no exception raised |
| D9  | README — Production cron management subsection  | How to update cPanel cron when `shift_hours` changes; how to run manually if missed; DST reminder — UAT finding 004b-3                         |
| D10 | `main.py` — `[SCHEDULE]` line in `run_health()` | Call existing `_shift_hours(config)`; print after `[TIMEZONE]`; non-blocking on error (AD-S004b-009)                                          |
| D11 | `main.py` — `[ENV TIME]` + `[TZ OFFSET]` lines  | subprocess `unset TZ && date`; offset from UTC offsets comparison; non-blocking on error (AD-S004b-010)                                        |

---

## UAT Checklist — Owner Executes on Server

| #   | Action                                 | Expected result                                                                                                                                                                                 |
|-----|----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| U01 | `git clone` + `pip install`            | No errors                                                                                                                                                                                       |
| U02 | `python main.py --health`              | All lines ✅; `[TIMEZONE]` shows Europe/Kyiv; `[SCHEDULE]` shows shift_hours; `[ENV TIME]` shows server local time; `[TZ OFFSET]` shows correct offset                                          |
| U03 | `python main.py --dry-run`             | Correct shifts listed for today                                                                                                                                                                 |
| U04 | `python main.py --production`          | Notification arrives in Telegram group                                                                                                                                                          |
| U05 | cPanel cron fires at scheduled time    | Notification arrives automatically, log written. **Test shortcut:** temporarily set the cron entry to `* * * * *`, wait one minute, verify notification and log, then restore the correct time. |
| U06 | Local Docker workflow                  | Still works unchanged — production deploy does not affect local setup                                                                                                                           |
| U07 | `python main.py --production` log      | `Clock drift OK` line present; no WARNING in normal conditions                                                                                                                                  |
| U08 | cPanel cron log shows correct timezone | Check log file written by the cron-fired run — `[TIMEZONE]` line must show `Europe/Kyiv`, not `UTC`. Confirms `TZ=` prefix is honoured by cPanel cron.                                          |

> **Note — log retention (AD-S004b-007):** Verify the weekly cleanup cron entry exists in cPanel UI after setup. Full functional verification requires waiting for the Sunday 03:00 EDT fire — confirm by checking that log files older than 30 days are absent after that date.

---

## UAT Findings Triage (2026-05-03)

| Finding | Title | Decision | Rationale |
|---------|-------|----------|-----------|
| 004b-1 | Extend health with shift schedule | 🔧 Fix in S004b — D10 | IT needs this to verify bot config without opening files; direct extension of S004b goal |
| 004b-2 | Extend health with env time and offset | 🔧 Fix in S004b — D11 | Required for IT to verify cron offset — core to S004b production operability |
| 004b-3 | README missing production cron management | 🔧 Fix in S004b — D9 | Gap in D1 deliverable; IT cannot operate production without this |
| 004b-4 | README cron table uses wrong server timezone | 🔧 Fix in S004b — D2 | Bug in D2 deliverable; cron entries calculated from wrong timezone will fire at wrong times |

---

## Open Questions

None. All OQs resolved:

| #    | Question        | Answer                                                                        |
|------|-----------------|-------------------------------------------------------------------------------|
| OQ-1 | cPanel username | Not needed — `.env` uses `<username>` placeholder; IT fills in at deploy time |
| OQ-2 | git available?  | ✅ Yes (`git --version` confirmed)                                             |
| OQ-3 | Server timezone | ~~UTC~~ **CORRECTED (2026-05-03):** Server runs EDT (UTC-4). Original answer was taken under `export TZ='UTC'` shell override which masked the real timezone. Cron times must subtract 7h from Kyiv EEST (UTC+3). DST adjustment required when either timezone changes clocks — verify offset at each transition. |

---

## Sprint Sign-off

| Role      | Name | Date       | Status                                                                |
|-----------|------|------------|-----------------------------------------------------------------------|
| Architect | AI   | 2026-05-03 | ✅ REVISED — AD-S004b-009/010 added; D10/D11 added; ready for Developer |
| Developer | AI   | 2026-05-03 | ✅ D1–D9 COMPLETE — D10/D11 pending                                     |
| QA        | AI   | 2026-05-02 | ✅ SIGNED OFF — QA-001/002/003 deferred to UAT                         |
| Owner     |      | 2026-05-03 | ⏸ IN PROGRESS — see `20260503_Sprint004b_UAT_ShiftNotificationBot.md` |
