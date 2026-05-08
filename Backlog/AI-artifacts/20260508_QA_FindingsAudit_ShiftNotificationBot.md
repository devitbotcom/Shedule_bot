# QA Findings Audit — All Sprints
**Date:** 2026-05-08
**Prepared by:** QA
**Purpose:** Full audit of all QA and UAT findings across S002–S006b2. Open items flagged for Architect review.

---

## Audit — Sprint 002

| ID             | Finding                                                                                | Status                                                                                                                                       |
|----------------|----------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| 002-1          | Add "what's next" to README bottom                                                     | ✅ Addressed (sprint plan in artifacts)                                                                                                       |
| 002-2          | QA/Dev/Arch role separation not solid                                                  | ✅ Process improved — role discipline memory established                                                                                      |
| 002-3 / TD-004 | Date column is integer day-of-month, not full date — day-of-month format not supported | ✅ DESIFED LOGIC — S006b2 scheduler now reads day numbers from Draft tab. POC1 XLSX parser still expects full date. Owner accepted at S002 UAT. |

---

## Audit — Sprint 003

| ID              | Finding                                             | Status                           |
|-----------------|-----------------------------------------------------|----------------------------------|
| BUG-001         | Double period on names ending with `.`              | ✅ Fixed S003                     |
| BUG-002         | `--employee` filter broke prev/next context         | ✅ Fixed S003                     |
| BUG-003         | Sent all month's shifts, not just today             | ✅ Fixed S003                     |
| BUG-004         | No rate limiting between sends                      | ✅ Fixed S003                     |
| BUG-005 / 003-1 | "Наступна зміна" always showed `-`                  | ✅ Fixed S004                     |
| 003-2           | Department not in message                           | ✅ Done S003                      |
| TD-001          | `run_production()` orchestrator has no tests        | 🔵 Deferred — no sprint assigned |
| TD-002          | `--employee` filter not covered by integration test | 🔵 Deferred                      |
| TD-003          | `--force` flag not covered by test                  | 🔵 Deferred                      |

---

## Audit — Sprint 004

| ID           | Finding                                         | Status                        |
|--------------|-------------------------------------------------|-------------------------------|
| BUG-S004-001 | Bot token exposed in log files                  | ✅ Fixed S004                  |
| BUG-S004-002 | Docker DNS failure                              | ✅ Fixed S004                  |
| 004-1        | No structured logs                              | ✅ Addressed                   |
| 004-2        | Two config sources for cron timing              | ✅ Addressed — `gen_crontab`   |
| 004-3        | Docker time quality check missing               | ✅ Done                        |
| 004-4        | Two Docker images built                         | ✅ Fixed                       |
| 004-05       | Day-type correction after send                  | ✅ Architect ruled — by design |
| 004-06       | No notification if cron restart after fire time | ✅ Addressed — README updated  |

---

## Audit — Sprint 004b

| ID                     | Finding                                            | Status                                                                                                                                  |
|------------------------|----------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| QA-001                 | `.env.example` Docker paths active by default      | ✅ Accepted                                                                                                                              |
| QA-002–005, QA-008–009 | README/DEPLOY.md gaps, gen_crontab hardcoded types | ✅ All fixed                                                                                                                             |
| QA-010                 | No test for custom shift type in `gen_crontab`     | ✅ Fixed — `test_gen_crontab_custom_shift_type_included` added                                                                           |
| 004b-1                 | Health output missing `shift_hours` block          | ✅ Implemented — `[SCHEDULE]` line in health output                                                                                      |
| 004b-2                 | Health missing env time and TZ offset              | ✅ Implemented (`[ENV TIME]`, `[TZ OFFSET]`) — but see 004b-6                                                                            |
| 004b-3                 | README missing cron instructions for production    | ✅ Addressed — DEPLOY.md updated                                                                                                         |
| 004b-4                 | README cron table used wrong server timezone       | ✅ Fixed — corrected to EDT                                                                                                              |
| 004b-5                 | `venv/` not in `.gitignore`                        | ✅ Fixed                                                                                                                                 |
| 004b-6                 | TZ offset display showed wrong info                | ✅ accepted                                                                                                                              |
| 004b-7                 | `--gen-crontab` printed entries but didn't install | ⚠️ **Status unclear** — code and tests show auto-install implemented; UAT artifact says "in progress". Owner confirmation not recorded. |

---

## Audit — Sprint 005

| ID             | Finding                                                   | Status                                                 |
|----------------|-----------------------------------------------------------|--------------------------------------------------------|
| F1             | `VALID_ROLES` unused import in test                       | 🔵 Deferred                                            |
| F2             | Weak assertion in `test_setrole_invalid_role_shows_usage` | 🔵 Deferred                                            |
| F3             | `run_bootstrap_it` hardcodes name "IT Admin"              | 🔵 Cosmetic, deferred                                  |
| F4             | No tests for `--register-webhook` / `--bootstrap-it`      | 🔵 Deferred                                            |
| F5             | CGI scaffolding not unit-tested                           | 🔵 Deferred                                            |
| F6             | `os.path.abspath` → `os.path.realpath` (symlink)          | ✅ Fixed                                                |
| F7             | CGI shebang couldn't see venv packages                    | ✅ Fixed                                                |
| F8             | `chmod 755` left git dirty                                | ✅ Fixed                                                |
| F9             | `yourdomain.com` placeholder not `<ALL_CAPS>`             | ✅ Fixed                                                |
| F10            | CGI not executing in `public_html/`                       | ✅ Superseded by F11                                    |
| F11            | CGI disabled server-wide — wrong hosting assumption       | ✅ Fixed — WSGI/Passenger                               |
| F12            | `tmp/` and `stderr.log` not in `.gitignore`               | ✅ Fixed                                                |
| F13            | `readme_WEBHOOK.md` troubleshooting incomplete            | 🟡 **Still open** — Developer item, no sprint assigned |
| PF1            | QA did not verify deployment procedure, only content      | 🔵 Process note — acknowledged                         |
| U005-5         | `/help` for IT role not verified in UAT                   | 🔵 Deferred — backlog 005-3                            |
| U005-8 / 005-2 | Bot responds to any message (too obsessive)               | 🔵 On hold — backlog 005-2                             |

---

## Audit — Sprint 006a

| ID    | Finding                                             | Status                                           |
|-------|-----------------------------------------------------|--------------------------------------------------|
| F1–F3 | Superseded by F5                                    | ✅                                                |
| F4    | ARCH spec wrong return type for `get_schedule_grid` | ✅ Fixed                                          |
| F5    | `schedule_sync.py` out of scope — wrong assumption  | ✅ Fixed — deleted                                |
| F6    | Missing `readme_GOOGLE_SHEETS.md`                   | ✅ Fixed                                          |
| 06-01 | Config keys not descriptive enough                  | ✅ Addressed in S006b — `scheduler_` prefix added |
| 06-2  | UAT console commands not copy-pastable              | 🟡 **Still open** — no sprint assigned           |

---

## Audit — Sprint 006b

| ID                | Finding                                         | Status                                                      |
|-------------------|-------------------------------------------------|-------------------------------------------------------------|
| F1                | ARCH spec wrong `generate_schedule` signature   | ✅ Fixed                                                     |
| F2                | `_cmd_draft` internals not tested               | ✅ Fixed — `test_cmd_draft.py` added                         |
| F3                | `readme_GOOGLE_SHEETS.md` stale troubleshooting | ✅ Fixed                                                     |
| F4                | ARCH OQ-1 not marked resolved                   | ✅ Fixed                                                     |
| 06b-01            | Bot silent — webhook health invisible           | 🔴 Open — KI-001, backlog 006b-01                           |
| 06b-02            | Integration failures not visible in health      | 🔴 Open — KI-002, backlog 006b-02                           |
| 06b-03 (CRITICAL) | Draft-by-bot copied Draft unchanged             | ✅ Fixed — separate scheduler keys                           |
| 06b-03 (LOW)      | No Google Sheet link in success reply           | 🟡 Open — KI-010, backlog 06b-03                            |
| 06b-04            | Period in initials rejected by V7 regex         | ✅ Fixed S006b2                                              |
| **U006b-1**       | `/draft` denied for non-Head                    | ✅ ACCEPTED                                                  |
| **U006b-2**       | `/draft` generates and writes tab               | ✅ ACCEPTED                                                  |
| **U006b-3**       | `/draft` called twice overwrites                | ⚠️  ACCEPTED  — but maybe need debouncing and progress info |
| **U006b-4**       | `/help` shows `/draft` for Head                 | ✅ ACCEPTED                                                  |
| **U006b-5**       | POC1 regression unaffected                      | ✅ ACCEPTED                                                  |

---

## Audit — Sprint 006b2

| ID            | Finding                                                  | Status                             |
|---------------|----------------------------------------------------------|------------------------------------|
| F1            | `import pytest` unused in test file                      | ✅ Fixed                            |
| F2 / KI-003   | `year_int=None` skips entire validation silently         | 🟡 Open — deferred S007+           |
| F3            | V5 `for…else` dead code                                  | ✅ Fixed                            |
| F4            | Stale assertion in T5a (`"має бути"`)                    | 🟡 **Open — Developer fix needed** |
| F5 / KI-004   | V6 inner `except` misses `TypeError` for `year_int=None` | 🟡 Open — deferred                 |
| F6 / KI-005   | V3 cascades when date column missing (noise)             | 🟡 Open — deferred                 |
| 06b2-1        | Mon-Fri not checked for `holiday`                        | ✅ Fixed — V6b added                |
| 06b2-2        | V5 message unreadable + warnings not in tab              | ✅ Fixed                            |
| 06b2-3        | V2 not firing on `None` cell                             | ✅ Fixed — `_cell()` helper         |
| AD-S006b2-008 | Warning message format unification                       | ✅ Done                             |
| **U006b2-1**  | Clean draft produces no warnings                         | ✅ OK                               |
| **U006b2-2**  | Warning for Sat/Sun not holiday                          | ✅ OK                 |
| **U006b2-3**  | Warning for empty day-type cell                          | ✅ OK                  |
| **U006b2-4**  | POC1 regression                                          | ✅ OK                               |

---

## Items for Architect review

The following open items require Architect decision, prioritisation, or design — they are not straightforward Developer fixes.

| #    | Item                                                      | Source              | Question for Architect                                                                                                                                                                        |
|------|-----------------------------------------------------------|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| A-01 | U006b-3, U006b-4, U006b-5 — S006b UAT never completed     | S006b UAT           | Three cases have no Owner sign-off. Should S006b be formally closed or is UAT re-run required before S006c?                                                                                   |
| A-02 | 004b-6 — TZ offset display wrong on server                | S004b UAT           | Was this resolved? Current health output shows `bot and server clocks match (Europe/Kyiv EDT UTC-4 vs server EDT UTC-4)` which is incorrect. Needs Architect to decide correct display logic. |
| A-03 | 004b-7 — `--gen-crontab` auto-install status              | S004b UAT           | Owner reported "must paste manually" — was automatic install implemented and confirmed, or still manual?                                                                                      |
| A-04 | KI-001 / 006b-01 — `--health` no Google Sheets check      | backlog             | Requires Arch design: which probes, what output format, what exit code on failure. Planned for S006c+.                                                                                        |
| A-05 | KI-002 / 006b-02 — No per-request logging for webhook     | backlog             | Requires Arch design: log format, log location, what constitutes an "attempt". Planned for S006c+.                                                                                            |
| A-06 | KI-003 / 006b2-01 — `year_int=None` skips validation      | backlog             | Arch decision: should V1/V2/V3/V5/V7 run without `year_int`? Or should bot warn Head that year was unreadable?                                                                                |
| A-07 | TD-001/002/003 — `run_production()` orchestrator untested | S003 QA             | Three deferred test gaps from S003. No sprint assigned. Arch to decide if these block any future work.                                                                                        |
| A-08 | F13 — `readme_WEBHOOK.md` troubleshooting incomplete      | S005 QA             | Covers: existing app, virtualenv conflict, reconfiguration. Developer fix, but Arch to confirm scope and assign to sprint.                                                                    |
| A-09 | 06b-03 (LOW) — No Google Sheet link in `/draft` reply     | backlog KI-010      | Simple addition (`GOOGLE_SHEET_ID` already in scope). Arch to confirm output format and assign sprint.                                                                                        |
| A-10 | QA-001 — `.env.example` Docker paths active by default    | S004b QA            | Never confirmed resolved. Arch to verify current state and decide if fix needed.                                                                                                              |
| A-11 | 06-2 — UAT console commands not copy-pastable             | S006a UAT           | Still open. Arch to decide if addressed in documentation sprint or backlog.                                                                                                                   |
| A-12 | KI-005 — V3 false cascade on missing date column          | S006b2 logic review | Skip V2/V3 loop when `day_col_idx is None`. Small code change — Arch to confirm approach before Developer implements.                                                                         |
