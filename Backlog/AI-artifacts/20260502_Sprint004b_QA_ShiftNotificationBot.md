# Sprint 004b — QA Review

**Sprint:** 004b  
**Role:** QA  
**Date:** 2026-05-02 (revised 2026-05-03)  
**Status:** ⏸ REOPENED — post-UAT findings added  
**Dev ref:** `20260502_Sprint004b_DEV_ShiftNotificationBot.md`  
**Arch ref:** `20260502_Sprint004b_ARCH_ShiftNotificationBot.md`

---

## Test Results

**Automated:** 87/87 passed (full suite, no regressions) — updated 2026-05-03  
**New tests:** `tests/test_clock_drift.py` — 4 cases; `tests/test_health_extensions.py` — 5 cases; `tests/test_gen_crontab.py` — 11 cases; all passing

---

## Findings

| # | Finding | Severity | Resolution |
|---|---------|----------|------------|
| QA-001 | `.env.example` Docker paths active by default — IT copying to server gets wrong paths | 🟡 | Deferred to Owner UAT |
| QA-002 | README P3 missing `cp data/schedule_mapping.json.example data/schedule_mapping.json` command | 🟡 | ✅ Resolved — present in DEPLOY.md P3 |
| QA-003 | README P5/P6 missing `cd ~/shift_bot` — fails if IT opens a new terminal session | 🟡 | ✅ Resolved — all DEPLOY.md commands include full `cd ~/Shedule_bot && source venv/bin/activate` prefix |
| QA-004 | `other` cron midnight-crossing not explained — IT may suspect misconfiguration | 🔵 | ✅ Resolved — note added to DEPLOY.md P8 |
| QA-005 | DEPLOY.md P6b ambiguous — "verify notifications send" implies messages always go out, but `--production` only sends if shifts exist for today's date | 🟡 | ✅ Fixed — P6b clarifies no-shifts-today case |
| QA-008 | `run_gen_crontab` hardcodes `("labor", "holiday", "other")` — custom shift types in `schedule_mapping.json` silently omitted from output | 🔴 | ✅ Fixed — `for st in hours.keys()` |
| QA-009 | DEPLOY.md P9b DST section still references old manual formula `cPanel time = shift_hours − ...` — should say "run `--gen-crontab`" | 🟡 | ✅ Fixed — DST procedure now uses `--health` + `--gen-crontab` |
| QA-010 | No test covers QA-008 fix — all `run_gen_crontab` tests mock exactly `{"labor", "holiday", "other"}`; custom shift type inclusion untested | 🔵 | Open — Developer to add one test case |

---

## Confirmed Clean

- `_check_clock_drift()` — non-blocking, HTTPS, correct type hint, called before send loop
- All 3 contract cases covered by tests: OK / drift > 300s / API unreachable
- RISK-001 mitigation present in README P12
- Security hardening two-step split correctly (deploy + post-first-run)
- DEV artifact and ARCH sign-off updated by Developer
- `_shift_time_to_server` — correct for all cases including midnight-crossing (01:25 → 18:25)
- `run_gen_crontab` — non-blocking on subprocess failure, outputs `<MIN>`/`<HOUR>` placeholders
- `run_gen_crontab` — install path correctly extracted from `XLSX_PATH`
- `run_verify_cron` — sends to `TELEGRAM_GROUP_CHAT_ID`, exits 0 on success / 1 on failure
- `cli.py` mutual exclusion guards present for `--gen-crontab` and `--verify-cron`
- README.md CLI table updated with new commands
- DEPLOY.md P8 replaced with `--gen-crontab` workflow
- DEPLOY.md P9 maintenance table updated
- DEPLOY.md P9b shift_hours-change workflow updated to use `--gen-crontab`
