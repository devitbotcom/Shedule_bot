# Sprint 004b — Developer Notes

**Sprint:** 004b  
**Role:** Developer  
**Date:** 2026-05-03  
**Status:** ✅ COMPLETE — D1–D11 done  
**Arch ref:** `20260502_Sprint004b_ARCH_ShiftNotificationBot.md`

---

## Deliverables

| #  | Deliverable                          | Status | Notes |
|----|--------------------------------------|--------|-------|
| D1 | README — Production Install (P0–P11) | ✅ | New `## For Production (cPanel)` section added |
| D2 | README — server-local cron conversion table | ✅ | P8; corrected 2026-05-03 — EDT times (−7h), formula, midnight-crossing note for `other`; was UTC (UAT finding 004b-4) |
| D3 | README — Production maintenance      | ✅ | P9 table maps Docker → venv commands |
| D4 | README — Security hardening          | ✅ | P7; two-step chmod (deploy + post-first-run) |
| D5 | README — Log retention cron          | ✅ | P8; weekly Sunday 03:00 EDT server local time |
| D9 | README — Production cron management  | ✅ | P9b; update workflow, manual run, DST procedure (UAT finding 004b-3) |
| D6 | `.env.example` — absolute paths      | ✅ | Production block added as commented section |
| D7 | `main.py` — `_check_clock_drift()`   | ✅ | Called at top of `run_production()`; HTTPS endpoint |
| D8  | `tests/test_clock_drift.py`                    | ✅ | 4 tests; 77/77 suite passing |
| D10 | `main.py` — `[SCHEDULE]` line in `run_health()` | ✅ | Calls `_shift_hours()`; non-blocking on error (AD-S004b-009) |
| D11 | `main.py` — `[ENV TIME]` + `[TZ OFFSET]` lines  | ✅ | subprocess `unset TZ`; offset comparison; non-blocking (AD-S004b-010) |
| D12 | `tests/test_health_extensions.py`              | ✅ | 5 tests; 82/82 suite passing |

---

## Code Changes

### `main.py`

- Added `import requests` (top-level import; already a project dependency)
- Added `_check_clock_drift() -> None` — queries `https://worldtimeapi.org/api/timezone/UTC`, logs delta; WARNING if > 300s; non-blocking on any exception
- Called `_check_clock_drift()` as first line of `run_production()`

### `tests/test_clock_drift.py` (new)

Four test cases:
1. `test_clock_drift_ok_logs_info` — API returns current time → INFO logged, no WARNING
2. `test_clock_drift_warning_when_delta_exceeds_threshold` — API returns time 400s in past → WARNING logged
3. `test_clock_drift_warning_when_api_unreachable` — Exception raised by requests → WARNING "skipped" logged
4. `test_clock_drift_does_not_raise_on_api_failure` — Exception raised → function returns cleanly, no propagation

### `.env.example`

Added commented production block showing absolute-path alternatives for `XLSX_PATH`, `DB_PATH`, `LOG_DIR` with `<username>` placeholder.

### `main.py` — post-UAT additions (2026-05-03)

- Added `import subprocess` (stdlib, no new dependency)
- `run_health()` — added `[SCHEDULE]` block: calls `_shift_hours(config)`, prints `labor/holiday/other` times; non-blocking on exception
- `run_health()` — added `[ENV TIME]` + `[TZ OFFSET]` block: subprocess `unset TZ; date; date +%z; date +%Z` to get server-native time; offset computed from bot's `utcoffset()` vs server's `date +%z`; non-blocking on exception

### `tests/test_health_extensions.py` (new)

Five test cases:
1. `test_schedule_line_shows_shift_hours` — `[SCHEDULE]` line appears with correct values
2. `test_schedule_line_shows_error_when_mapping_unreadable` — `_shift_hours` raises → `[SCHEDULE] ❌` printed, no crash
3. `test_env_time_and_offset_shown` — subprocess returns fake EDT output → `[ENV TIME]` and `[TZ OFFSET]` present
4. `test_env_time_shows_error_when_subprocess_fails` — subprocess raises → `[ENV TIME] ❌` printed
5. `test_env_time_error_does_not_raise` — subprocess raises → only `SystemExit` from `run_health`, no propagation

### `README.md`

- Added `## For Production (cPanel — Namecheap)` section (P0–P12) *(original)*
- Added P12 Clock drift monitor — explains "skipped" vs "drift" warnings (RISK-001 mitigation)
- Removed "Coming next — S004b" trailer
- **Post-UAT correction (2026-05-03):** P8 cron table rewritten for EDT server (was UTC); formula `shift_hours − 7h` added; midnight-crossing note for `other` entry added; log retention comment updated to "EDT server local time"
- **Post-UAT addition (2026-05-03):** P9b "Managing cPanel cron entries" — update workflow, manual run procedure, DST verification steps

---

## Test Results

```
82 passed in 0.49s
```

All pre-existing tests continue to pass. No regressions.
