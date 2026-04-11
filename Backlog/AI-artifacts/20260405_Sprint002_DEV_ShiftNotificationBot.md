# Sprint 002 — Developer Deliverables
**Sprint:** 002  
**Role:** Developer  
**Date:** 2026-04-05  
**Status:** ✅ IMPLEMENTED — handed to QA  
**Arch ref:** [`20260405_Sprint002_ARCH_ShiftNotificationBot.md`](20260405_Sprint002_ARCH_ShiftNotificationBot.md)  
**QA ref:** [`20260405_Sprint002_QA_ShiftNotificationBot.md`](20260405_Sprint002_QA_ShiftNotificationBot.md)

---

## Deliverables — Files Created

All files are in the `Shedule_bot/` submodule root.

| File | Purpose | Status |
|---|---|---|
| `requirements.txt` | Pinned dependencies | ✅ |
| `.env.example` | Environment variable template | ✅ |
| `models.py` | `Shift`, `ShiftContext`, `RunMode` dataclasses | ✅ |
| `config.py` | Env var loading and validation | ✅ |
| `cli.py` | Argument parsing, returns `RunMode` | ✅ |
| `db.py` | SQLite init, schema, all read/write helpers | ✅ |
| `schedule_parser.py` | XLSX parser with mtime guard | ✅ |
| `shift_logic.py` | Pure prev/next shift computation | ✅ |
| `main.py` | Entry point — health, dry-run, reload-schedule modes | ✅ (S003 adds production mode) |
| `messenger/__init__.py` | Package marker | ✅ |
| `messenger/gateway.py` | `MessengerGateway` abstract interface | ✅ |
| `messenger/telegram_adapter.py` | Stub — raises `NotImplementedError` (S003) | ✅ |
| `messenger/viber_adapter.py` | Stub — raises `NotImplementedError` (P2) | ✅ |
| `tests/__init__.py` | Package marker | ✅ |
| `tests/test_config.py` | Unit tests for config.py | ✅ |
| `tests/test_cli.py` | Unit tests for cli.py | ✅ |
| `tests/test_db.py` | Unit tests for db.py | ✅ |
| `tests/test_schedule_parser.py` | Unit tests for schedule_parser.py | ✅ |
| `tests/test_shift_logic.py` | Unit tests for shift_logic.py | ✅ |
| `tests/create_fixture.py` | One-time script to generate XLSX fixture | ✅ |
| `tests/fixtures/sample_schedule.xlsx` | Test fixture — 5 shifts, 4 employees | ✅ |

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

## Out of Scope — Deferred to S003

- `production` mode in `main.py`
- `TelegramAdapter.send()` implementation
- Full boot sequence steps ③–⑦

## Out of Scope — Deferred to P2

- `ViberAdapter.send()` implementation
