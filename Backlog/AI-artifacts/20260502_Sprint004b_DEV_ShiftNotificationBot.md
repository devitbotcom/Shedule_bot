# Sprint 004b — Developer Notes

**Sprint:** 004b  
**Role:** Developer  
**Date:** 2026-05-03  
**Status:** ✅ COMPLETE — D1–D15 implemented; QA-005/008/009 fixed  
**Arch ref:** `20260502_Sprint004b_ARCH_ShiftNotificationBot.md`

---

## Deliverables

| #   | Deliverable                                          | Status | Notes |
|-----|------------------------------------------------------|--------|-------|
| D1  | DEPLOY.md — Production Install (P0–P12)              | ✅ | Split from README.md; standalone production guide |
| D2  | DEPLOY.md — server-local cron times via `--gen-crontab` | ✅ | P8 replaced with command; was manual table (UAT 004b-4) |
| D3  | DEPLOY.md — Production maintenance table             | ✅ | P9; includes `--gen-crontab` entry |
| D4  | DEPLOY.md — Security hardening                       | ✅ | P7; two-step chmod (deploy + post-first-run) |
| D5  | DEPLOY.md — Log retention cron                       | ✅ | Included in `--gen-crontab` output |
| D6  | `.env.example` — absolute path placeholders          | ✅ | Production block added as commented section |
| D7  | `main.py` — `_check_clock_drift()`                   | ✅ | Called at top of `run_production()`; HTTPS endpoint |
| D8  | `tests/test_clock_drift.py`                          | ✅ | 4 tests |
| D9  | DEPLOY.md — Production cron management (P9b)         | ✅ | Update workflow uses `--gen-crontab`; DST procedure; manual run (UAT 004b-3) |
| D10 | `main.py` — `[SCHEDULE]` line in `run_health()`      | ✅ | Calls `_shift_hours()`; non-blocking (AD-S004b-009) |
| D11 | `main.py` — `[ENV TIME]` + `[TZ OFFSET]` lines       | ✅ | subprocess `unset TZ`; offset comparison; non-blocking (AD-S004b-010) |
| D11b| `tests/test_health_extensions.py`                    | ✅ | 5 tests covering D10 and D11 |
| D12 | `cli.py` + `main.py` — `--gen-crontab` command       | ✅ | Reads shift_hours + server offset; prints 5 cron entries (AD-S004b-011) |
| D13 | `cli.py` + `main.py` — `--verify-cron` command       | ✅ | Sends Telegram confirmation; exits 0/1 (AD-S004b-012) |
| D14 | DEPLOY.md P8 — replaced manual table with `--gen-crontab` | ✅ | QA-006/007 resolved |
| D15 | `tests/test_gen_crontab.py`                          | ✅ | 11 tests; QA-008 open (hardcoded shift types) |

---

## Code Changes

### `config.py` (UAT 004b-6 fix)

- Added `import time`
- Added `time.tzset()` call after `load_dotenv()` when `TZ` env var is set — ensures `datetime.now()` uses the correct timezone when running manually without shell TZ prefix

### `main.py`

- Added `import subprocess` (stdlib, no new dependency)
- Added `_check_clock_drift() -> None` — queries `https://worldtimeapi.org/api/timezone/UTC`, logs delta; WARNING if > 300s; non-blocking
- Called `_check_clock_drift()` as first line of `run_production()`
- Added `[SCHEDULE]` block in `run_health()`: calls `_shift_hours(config)`, prints labor/holiday/other times; non-blocking
- Added `[ENV TIME]` + `[TZ OFFSET]` block in `run_health()`: subprocess `unset TZ; date; date +%z; date +%Z`; offset comparison; both lines printed after all calculations; non-blocking
- Added `_shift_time_to_server(kyiv_hhmm, bot_offset_h, server_offset_h) -> tuple` — pure conversion function
- Added `run_gen_crontab(config)` — reads shift_hours + server offset via subprocess; prints 5 ready-to-paste cron entries including ~5-min verification entry; non-blocking on offset failure
- Added `run_verify_cron(config)` — sends `✅ Cron active` to `TELEGRAM_GROUP_CHAT_ID`; exits 0/1
- Added dispatch branches in `main()` for `gen_crontab` and `verify_cron` modes

### `cli.py`

- Added `--gen-crontab` argument
- Added `--verify-cron` argument
- Added mutual exclusion guards for both new modes
- Added mode determination branches (before `reload_schedule`)

### `models.py`

- Updated `mode` field comment to include `'gen_crontab'` and `'verify_cron'`

### `tests/test_clock_drift.py` (new)

4 tests: clock OK → INFO; delta > 300s → WARNING; API unreachable → WARNING; no exception raised on failure.

### `tests/test_health_extensions.py` (new)

5 tests: `[SCHEDULE]` shows values; `[SCHEDULE]` error case; `[ENV TIME]`/`[TZ OFFSET]` shown; subprocess fail → error line; no-raise guarantee.

### `tests/test_gen_crontab.py` (replaced — was Docker gen_crontab.py tests)

11 tests:
- 4 pure unit tests for `_shift_time_to_server`: labor/holiday/other conversions, midnight-crossing, same-timezone
- 5 tests for `run_gen_crontab`: all shift types present, verify entry present, install path correct, placeholder on offset failure, log retention present
- 2 tests for `run_verify_cron`: sends to correct chat_id, exits 1 on failure

### `README.md`

- Rewritten to contain Docker/local setup only (sections 0–10 + developer reference)
- Added cross-reference link to DEPLOY.md
- Added `--gen-crontab` and `--verify-cron` to CLI reference table

### `DEPLOY.md` (new file, split from README.md)

- All production content (P0–P12) moved here
- Uses `Shedule_bot` as folder name throughout (actual `git clone` output)
- P6b added — first production run step
- P8 replaced with `--gen-crontab` command
- P9b updated — shift_hours change workflow uses `--gen-crontab`; DST procedure present
- Cross-reference link to README.md at top

### `.gitignore`

- Added `venv/` under `# Python` section (UAT finding 004b-5)

---

## Test Results

```
87 passed in 0.38s
```

All pre-existing tests continue to pass. No regressions.

---

## QA Fixes

| # | Issue | Fix |
|---|-------|-----|
| QA-008 | `run_gen_crontab` hardcoded shift types | Changed `for st in ("labor", "holiday", "other")` → `for st in hours.keys()` |
| QA-009 | DEPLOY.md P9b DST section had old manual formula | Replaced with `--health` + `--gen-crontab` workflow |
| QA-005 | DEPLOY.md P6b ambiguous about when messages are sent | Clarified: messages sent only if shifts exist today; DB created either way |
