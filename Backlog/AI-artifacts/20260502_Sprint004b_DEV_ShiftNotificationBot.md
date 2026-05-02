# Sprint 004b — Developer Notes

**Sprint:** 004b  
**Role:** Developer  
**Date:** 2026-05-02  
**Status:** ✅ COMPLETE  
**Arch ref:** `20260502_Sprint004b_ARCH_ShiftNotificationBot.md`

---

## Deliverables

| #  | Deliverable                          | Status | Notes |
|----|--------------------------------------|--------|-------|
| D1 | README — Production Install (P0–P11) | ✅ | New `## For Production (cPanel)` section added |
| D2 | README — UTC conversion table        | ✅ | In P8; includes DST note |
| D3 | README — Production maintenance      | ✅ | P9 table maps Docker → venv commands |
| D4 | README — Security hardening          | ✅ | P7; two-step chmod (deploy + post-first-run) |
| D5 | README — Log retention cron          | ✅ | P8; weekly Sunday 03:00 UTC entry |
| D6 | `.env.example` — absolute paths      | ✅ | Production block added as commented section |
| D7 | `main.py` — `_check_clock_drift()`   | ✅ | Called at top of `run_production()`; HTTPS endpoint |
| D8 | `tests/test_clock_drift.py`          | ✅ | 4 tests; 77/77 suite passing |

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

### `README.md`

- Added `## For Production (cPanel — Namecheap)` section (P0–P12)
- Added P12 Clock drift monitor — explains "skipped" vs "drift" warnings (RISK-001 mitigation)
- Removed "Coming next — S004b" trailer

---

## Test Results

```
77 passed in 0.71s
```

All pre-existing tests continue to pass. No regressions.
