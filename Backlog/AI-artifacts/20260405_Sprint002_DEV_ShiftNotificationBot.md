# Sprint 002 — Developer Deliverables
**Sprint:** 002  
**Role:** Developer  
**Date:** 2026-04-05 (revised 2026-04-30)  
**Status:** ⏳ REVISED — RED FLAGS resolved, awaiting Docker test run + Owner UAT  
**Arch ref:** [`20260405_Sprint002_ARCH_ShiftNotificationBot.md`](20260405_Sprint002_ARCH_ShiftNotificationBot.md)  
**QA ref:** [`20260405_Sprint002_QA_ShiftNotificationBot.md`](20260405_Sprint002_QA_ShiftNotificationBot.md)

---

## Deliverables — Files Created

All files are in the `Shedule_bot/` submodule root.

| File                                  | Purpose                                              | Status                        |
|---------------------------------------|------------------------------------------------------|-------------------------------|
| `requirements.txt`                    | Pinned dependencies                                  | ✅                             |
| `.env.example`                        | Environment variable template                        | ✅                             |
| `models.py`                           | `Shift`, `ShiftContext`, `RunMode` dataclasses       | ✅                             |
| `config.py`                           | Env var loading and validation                       | ✅                             |
| `cli.py`                              | Argument parsing, returns `RunMode`                  | ✅                             |
| `db.py`                               | SQLite init, schema, all read/write helpers          | ✅                             |
| `schedule_parser.py`                  | XLSX parser with mtime guard                         | ✅                             |
| `shift_logic.py`                      | Pure prev/next shift computation                     | ✅                             |
| `main.py`                             | Entry point — health, dry-run, reload-schedule modes | ✅ (S003 adds production mode) |
| `messenger/__init__.py`               | Package marker                                       | ✅                             |
| `messenger/gateway.py`                | `MessengerGateway` abstract interface                | ✅                             |
| `messenger/telegram_adapter.py`       | Stub — raises `NotImplementedError` (S003)           | ✅                             |
| `messenger/viber_adapter.py`          | Stub — raises `NotImplementedError` (P2)             | ✅                             |
| `tests/__init__.py`                   | Package marker                                       | ✅                             |
| `tests/test_config.py`                | Unit tests for config.py                             | ✅                             |
| `tests/test_cli.py`                   | Unit tests for cli.py                                | ✅                             |
| `tests/test_db.py`                    | Unit tests for db.py                                 | ✅                             |
| `tests/test_schedule_parser.py`       | Unit tests for schedule_parser.py                    | ✅                             |
| `tests/test_shift_logic.py`           | Unit tests for shift_logic.py                        | ✅                             |
| `tests/create_fixture.py`             | One-time script to generate XLSX fixture             | ✅                             |
| `tests/fixtures/sample_schedule.xlsx` | Test fixture — 5 shifts, 4 employees                 | ✅                             |

---

## Directory Structure (as built)

```
Shedule_bot/
├── main.py
├── models.py
├── config.py
├── cli.py
├── db.py
├── schedule_parser.py
├── shift_logic.py
├── requirements.txt
├── .env.example
├── messenger/
│   ├── __init__.py
│   ├── gateway.py
│   ├── telegram_adapter.py   ← stub, S003
│   └── viber_adapter.py      ← stub, P2
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_cli.py
│   ├── test_db.py
│   ├── test_schedule_parser.py
│   ├── test_shift_logic.py
│   ├── create_fixture.py
│   └── fixtures/
│       └── sample_schedule.xlsx
└── Backlog/
    └── AI-artifacts/
```

---

## Implementation Notes

**`models.py` — shared dataclasses**  
Extracted to a separate module so all other modules import from one place. No circular imports.

**`config.py` — fail fast**  
Reports all missing variables at once (not just the first one) before calling `sys.exit(1)`. Owner sees the full picture in one run.

**`cli.py` — argparse with combination validation**  
Invalid flag combinations (`--force` without `--production`, `--dry-run` with `--production`) exit with code 2 and print usage automatically via `parser.error()`.

**`db.py` — WAL mode on every connection**  
Each function opens and closes its own connection. WAL mode and foreign keys enabled on every open. `was_notified()` checks `status='ok'` only — a failed send does not block retry.

**`schedule_parser.py` — mtime guard**  
Checks file age before opening. Raises `RuntimeError` (not `SystemExit`) so callers can report `[XLSX] ❌` cleanly. Date conversion handles both `DD-MM-YYYY` strings and `datetime` objects (openpyxl returns either depending on cell format).

**`shift_logic.py` — pure function**  
No imports beyond stdlib. `DUTY_ORDER` dict used as secondary sort key within the same date. Scans linearly — sufficient for PoC staff volumes.

**`main.py` — S002 scope only**  
Handles `health`, `dry_run`, and `reload_schedule` modes. `production` mode raises `NotImplementedError` — implemented in S003. Logging initialised after config load (not at import time).

---

---

## [RED FLAG] Revision Log — 2026-04-30

The 2026-04-30 review session (see `20260430_Discussion_PRL_XLSX_Review_ShiftNotificationBot.md`) revealed that the S002 ARCH was written before the real XLSX structure was examined. All affected files were corrected without changing the S003/P2 scope boundary.

| Issue                      | Old (S002 ARCH)                            | Corrected                                          |
|----------------------------|--------------------------------------------|----------------------------------------------------|
| Employee registry source   | XLSX Sheet 2                               | `contacts.json` (server-side, not in Git)          |
| XLSX structure             | Flat: one employee per row                 | Grid: one duty doctor per dept column per date row |
| Header row                 | Row 1                                      | Row 6 (rows 1–5 are title block)                   |
| Column names               | `shift_date`, `employee_name`, `duty_type` | `Дата`, `Day-type`, department name per column     |
| `Shift` model fields       | `duty_type`, `role`, `location`            | `day_type`, `department`                           |
| Env variable               | `LOCATION_DEFAULT`                         | `CONTACTS_PATH`                                    |
| `shift_logic.py` match key | `role` + `location`                        | `department`                                       |
| Docker local dev env       | not present                                | `Dockerfile` + `docker-compose.yml` added          |

### Files changed in revision

| File                                  | Change                                                       |
|---------------------------------------|--------------------------------------------------------------|
| `models.py`                           | `duty_type`/`role`/`location` → `day_type`/`department`      |
| `config.py`                           | `LOCATION_DEFAULT` → `CONTACTS_PATH`                         |
| `.env.example`                        | updated accordingly                                          |
| `schedule_parser.py`                  | complete rewrite — grid parser, contacts.json, row 6 headers |
| `shift_logic.py`                      | match by `department`; removed `DUTY_ORDER`                  |
| `main.py`                             | updated `parse_schedule` calls and dry-run output            |
| `requirements.txt`                    | added `pytest==8.3.5`                                        |
| `Dockerfile`                          | new — python:3.11.14-slim                                    |
| `docker-compose.yml`                  | new — local dev env                                          |
| `tests/test_config.py`                | `LOCATION_DEFAULT` → `CONTACTS_PATH`                         |
| `tests/test_schedule_parser.py`       | rewritten for grid fixture                                   |
| `tests/test_shift_logic.py`           | rewritten for `department` match                             |
| `tests/create_fixture.py`             | rewritten — grid XLSX + contacts.json                        |
| `tests/fixtures/contacts.json`        | new file                                                     |
| `tests/fixtures/sample_schedule.xlsx` | regenerated — must run `create_fixture.py` once              |

---

## Dev Workflow (Docker)

```bash
docker compose build
docker compose run --rm bot python tests/create_fixture.py
docker compose run --rm bot pytest
docker compose run --rm bot python main.py          # health check (requires .env)
docker compose run --rm bot python main.py --dry-run
```

---

## Out of Scope — Deferred to S003

- `production` mode in `main.py`
- `TelegramAdapter.send()` implementation
- Full boot sequence steps ③–⑦

## Out of Scope — Deferred to P2

- `ViberAdapter.send()` implementation
