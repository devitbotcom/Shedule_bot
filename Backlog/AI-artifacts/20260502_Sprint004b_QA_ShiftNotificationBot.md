# Sprint 004b — QA Review

**Sprint:** 004b  
**Role:** QA  
**Date:** 2026-05-02  
**Status:** ✅ SIGNED OFF — 3 findings deferred to Owner UAT  
**Dev ref:** `20260502_Sprint004b_DEV_ShiftNotificationBot.md`  
**Arch ref:** `20260502_Sprint004b_ARCH_ShiftNotificationBot.md`

---

## Test Results

**Automated:** 77/77 passed (full suite, no regressions)  
**New tests:** `tests/test_clock_drift.py` — 4 cases, all passing

---

## Findings

| # | Finding | Severity | Resolution |
|---|---------|----------|------------|
| QA-001 | `.env.example` Docker paths active by default — IT copying to server gets wrong paths | 🟡 | Deferred to Owner UAT |
| QA-002 | README P3 missing `cp data/schedule_mapping.json.example data/schedule_mapping.json` command | 🟡 | Deferred to Owner UAT |
| QA-003 | README P5/P6 missing `cd ~/shift_bot` — fails if IT opens a new terminal session | 🟡 | Deferred to Owner UAT |
| QA-004 | `other` cron midnight-crossing not explained — IT may suspect misconfiguration | 🔵 | Recorded as RISK-002 |

---

## Confirmed Clean

- `_check_clock_drift()` — non-blocking, HTTPS, correct type hint, called before send loop
- All 3 contract cases covered by tests: OK / drift > 300s / API unreachable
- RISK-001 mitigation present in README P12
- Security hardening two-step split correctly (deploy + post-first-run)
- DST warning present in P8
- DEV artifact and ARCH sign-off updated by Developer
