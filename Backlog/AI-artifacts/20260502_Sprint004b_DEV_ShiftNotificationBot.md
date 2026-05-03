# Sprint 004b — Developer Notes

**Sprint:** 004b  
**Role:** Developer  
**Date:** 2026-05-03  
**Status:** ✅ COMPLETE — D1–D16 implemented; QA-005/008/009/010 fixed; AD-S004b-013/014 implemented  
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
| D12 | `cli.py` + `main.py` — `--gen-crontab` command       | ✅ | Installs via `crontab`; `# shedule_bot` marker; idempotent; fallback to print (AD-S004b-011/013) |
| D13 | `cli.py` + `main.py` — `--verify-cron` command       | ✅ | Sends Telegram confirmation; self-removes from crontab; exits 0/1 (AD-S004b-012/014) |
| D14 | DEPLOY.md P8/P9b — auto-install; no cPanel UI needed | ✅ | UAT 004b-7 resolved |
| D15 | `tests/test_gen_crontab.py`                          | ✅ | 16 tests (was 11); QA-010 closed |
| D16 | `tests/test_gen_crontab.py` — crontab install tests  | ✅ | install, idempotency, fallback, self-remove (AD-S004b-013/014) |

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
- Added `run_gen_crontab(config)` — reads shift_hours + server offset; builds entries with `# shedule_bot` marker; installs via `crontab -l` / `crontab -` (idempotent: removes old shedule_bot lines first); falls back to printing if install fails; non-blocking on offset failure
- Added `run_verify_cron(config)` — sends `✅ Cron active` to `TELEGRAM_GROUP_CHAT_ID`; self-removes `--verify-cron` entry from crontab after send; exits 0/1
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

16 tests (was 11):
- 4 pure unit tests for `_shift_time_to_server`
- 9 tests for `run_gen_crontab`: existing 5 updated to check `_CrontabCapture.installed` (not stdout); 4 new: installs via crontab, idempotent, fallback prints on crontab failure, custom shift type included (closes QA-010)
- 3 tests for `run_verify_cron`: existing 2 updated; 1 new self-remove test

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
92 passed in 0.45s
```

All pre-existing tests continue to pass. No regressions.

---

## QA Fixes

| # | Issue | Fix |
|---|-------|-----|
| QA-008 | `run_gen_crontab` hardcoded shift types | Changed `for st in ("labor", "holiday", "other")` → `for st in hours.keys()` |
| QA-009 | DEPLOY.md P9b DST section had old manual formula | Replaced with `--health` + `--gen-crontab` workflow |
| QA-005 | DEPLOY.md P6b ambiguous about when messages are sent | Clarified: messages sent only if shifts exist today; DB created either way |
| QA-010 | No test for custom shift type inclusion in gen_crontab | Added `test_gen_crontab_custom_shift_type_included` |
| UAT-007 | `--gen-crontab` print-only, manual cPanel required | AD-S004b-013/014: auto-install via `crontab`; self-removing verify entry |
