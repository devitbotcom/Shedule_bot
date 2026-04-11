# Sprint 002 — Architecture
**Sprint:** 002  
**Role:** Architect  
**Date:** 2026-04-05  
**Status:** ✅ APPROVED  
**Scope:** Foundation — scaffold, config, CLI, DB, XLSX parser, shift logic  
**Depends on:** S001 ARCH (closed)  
**Blocks:** S003

---

## Sprint Goal

Deliver a fully working local foundation with zero network calls.  
By the end of this sprint, the Owner can run the script locally and observe correct shift data output, a working health check, and a populated SQLite DB — without any messenger tokens configured.

---

## Scope Boundaries

| In scope                                             | Out of scope                          |
|------------------------------------------------------|---------------------------------------|
| Project scaffold and directory structure             | Any messenger calls (Telegram, Viber) |
| `config.py` — env var loading and validation         | `main.py` orchestrator (S003)         |
| `cli.py` — argument parsing and mode detection       | Deployment to Namecheap (S004)        |
| `db.py` — SQLite init, schema, helpers               | Viber adapter (P2)                    |
| `schedule_parser.py` — XLSX reading and validation   | Receipt tracking write path (P2)      |
| `shift_logic.py` — pure prev/next computation        | Any real messenger token in `.env`    |
| Health check output (partial: config, DB, XLSX only) |                                       |
| `--dry-run` mode (preview output)                    |                                       |
| Unit tests for all five modules                      |                                       |

---

## Data Models

All models use `dataclasses`. No third-party typing libraries — Python 3.11 stdlib only.

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Shift:
    employee_name: str
    role:          str
    duty_type:     str   # 'Day' | 'Night' | '24h'
    shift_date:    str   # ISO 8601 date: 'YYYY-MM-DD'
    location:      str   # 'default' for PoC — reserved for v2 multi-ward
    messenger:     str   # 'telegram' | 'viber'
    contact_id:    str   # Telegram chat_id or Viber user ID

@dataclass
class ShiftContext:
    shift:          Shift
    prev_colleague: Optional[Shift]  # None → display as '-'
    next_colleague: Optional[Shift]  # None → display as '-'

@dataclass
class RunMode:
    mode:     str            # 'health' | 'dry_run' | 'production' | 'reload_schedule'
    employee: Optional[str]  # set only for --employee flag
    force:    bool           # True only for --force flag
    dry_run:  bool           # True for --dry-run flag
```

---

## Module Contracts

### `config.py`

**Responsibility:** Load all env variables at startup. Fail fast on any missing value.

**Required env variables:**

| Variable             | Description                                     |
|----------------------|-------------------------------------------------|
| `XLSX_PATH`          | Absolute path to `schedule.xlsx`                |
| `DB_PATH`            | Absolute path to `shift_bot.db`                 |
| `LOG_DIR`            | Absolute path to log directory                  |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (may be placeholder in S002) |
| `LOCATION_DEFAULT`   | Location label for PoC — e.g. `"Ward A"`        |

**Interface:**
```python
def load_config() -> dict:
    """Load and validate all env variables.
    Raises SystemExit(1) with a clear message if any required variable is missing."""
```

---

### `cli.py`

**Responsibility:** Parse `sys.argv`, return a `RunMode` object. No business logic here.

**Valid flag combinations:**

| Invocation                               | `mode`            | `employee` | `force` | `dry_run` |
|------------------------------------------|-------------------|------------|---------|-----------|
| `main.py`                                | `health`          | None       | False   | False     |
| `main.py --dry-run`                      | `dry_run`         | None       | False   | True      |
| `main.py --production`                   | `production`      | None       | False   | False     |
| `main.py --production --employee "Name"` | `production`      | `"Name"`   | False   | False     |
| `main.py --production --force`           | `production`      | None       | True    | False     |
| `main.py --reload-schedule`              | `reload_schedule` | None       | False   | False     |
| `main.py --reload-schedule --dry-run`    | `reload_schedule` | None       | False   | True      |

Invalid combinations → print usage message, `exit(1)`.

**Interface:**
```python
def parse_args() -> RunMode:
    """Parse sys.argv and return a RunMode. Exits with code 1 on invalid input."""
```

---

### `db.py`

**Responsibility:** All SQLite access. No other module may contain SQL.

**Schema** (created on first run, idempotent):
```sql
CREATE TABLE IF NOT EXISTS notifications (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name TEXT    NOT NULL,
    shift_date    TEXT    NOT NULL,
    messenger     TEXT    NOT NULL,
    sent_at       TEXT    NOT NULL,
    status        TEXT    NOT NULL,
    error         TEXT
);

CREATE TABLE IF NOT EXISTS receipts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name TEXT    NOT NULL,
    replied_at    TEXT    NOT NULL,
    message       TEXT
);
```

**Interface:**
```python
def init_db(db_path: str) -> None:
    """Create DB file, apply schema, enable WAL mode. Idempotent."""

def was_notified(db_path: str, employee_name: str, shift_date: str) -> bool:
    """Return True if a successful notification exists for this (employee, shift_date)."""

def record_notification(db_path: str, employee_name: str, shift_date: str,
                        messenger: str, status: str, error: str = None) -> None:
    """Insert one row into notifications table."""

def get_last_run_summary(db_path: str) -> dict:
    """Return {'sent_at': str, 'total': int, 'ok': int, 'fail': int} of the most recent run batch."""

def get_pending_count(db_path: str, shifts: list) -> int:
    """Return count of shifts not yet notified (for health check display)."""

def clear_notifications_for_dates(db_path: str, dates: list) -> int:
    """Delete notification records for given shift_dates. Returns count deleted."""
```

---

### `schedule_parser.py`

**Responsibility:** Read and validate `schedule.xlsx`. Return typed `Shift` objects. Perform mtime guard.

**Expected XLSX structure:**

Sheet 1 — Schedule:

| Column          | Content                     |
|-----------------|-----------------------------|
| `shift_date`    | Date in `DD-MM-YYYY` format |
| `employee_name` | Full name string            |
| `duty_type`     | `Day` / `Night` / `24h`     |

Sheet 2 — Employee Registry:

| Column          | Content                           |
|-----------------|-----------------------------------|
| `employee_name` | Full name (join key to Sheet 1)   |
| `role`          | Role string                       |
| `messenger`     | `telegram` or `viber`             |
| `contact_id`    | Telegram chat_id or Viber user ID |

**Interface:**
```python
def check_file_freshness(xlsx_path: str, threshold_seconds: int = 60) -> None:
    """Raises RuntimeError if file mtime is within threshold_seconds of now."""

def parse_schedule(xlsx_path: str, location_default: str) -> list:
    """Parse both sheets, merge on employee_name, return List[Shift].
    Raises SystemExit(1) on missing column, missing employee in registry, or unreadable file."""
```

---

### `shift_logic.py`

**Responsibility:** Pure computation. Accept a list of `Shift` objects, return `ShiftContext` for each. Zero I/O.

**Algorithm:**
1. Sort shifts by `shift_date` ascending
2. For each shift, find prev and next by scanning the sorted list for the nearest entries where `role == shift.role AND location == shift.location`
3. If none found: `prev_colleague = None`, `next_colleague = None`

**Interface:**
```python
def compute_contexts(shifts: list) -> list:
    """Accept List[Shift], return List[ShiftContext].
    Pure function — no I/O, no network, no logging."""
```

---

## Health Check Output (S002 scope — partial)

In S002 the health check covers config, DB, and XLSX only.  
Messenger checks (Telegram, Viber) are added in S003.

```
[CONFIG]  ✅ all variables loaded
[DB]      ✅ shift_bot.db reachable, schema valid
[XLSX]    ✅ schedule.xlsx found — N employees, N shift dates
[LAST RUN] no runs recorded yet
[PENDING]  N employees pending notification
```

Exit code 0 if all ✅. Exit code 1 if any ❌.

---

## Acceptance Criteria

- [ ] `python main.py` → health check output, exit 0
- [ ] `python main.py` with missing env var → ❌ config, exit 1
- [ ] `python main.py --dry-run` → shift data printed per employee, zero sends, zero DB writes
- [ ] `python main.py --reload-schedule` → parses XLSX, clears dedup records for those dates
- [ ] `python main.py --reload-schedule --dry-run` → shows what would be cleared, no DB change
- [ ] All unit tests pass with no network calls and no real `.env`
- [ ] `shift_bot.db` created automatically on first run
- [ ] XLSX mtime guard triggers correctly when file is freshly modified

---

## Risks

| Risk                                                     | Mitigation                                                                               |
|----------------------------------------------------------|------------------------------------------------------------------------------------------|
| XLSX column names may differ from spec                   | `schedule_parser.py` must log exact column name on mismatch — Owner adjusts XLSX headers |
| `contact_id` may be empty for some employees             | Log employee name and skip — do not crash                                                |
| Python 3.11.14 not yet set up in venv on Owner's machine | S002 is local — Owner sets up venv using `requirements.txt` as part of UAT               |
