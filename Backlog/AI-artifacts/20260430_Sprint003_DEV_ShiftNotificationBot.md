# Sprint 003 — Developer Deliverables
**Sprint:** 003  
**Role:** Developer  
**Date:** 2026-04-30  
**Status:** ⏳ DEV complete — awaiting QA + Owner UAT  
**Arch ref:** [`20260430_Sprint003_ARCH_ShiftNotificationBot.md`](20260430_Sprint003_ARCH_ShiftNotificationBot.md)  
**Plan ref:** [`2026-04-30_Development_Plan.md`](../2026-04-30_Development_Plan.md)

---

## Scope

Implement Telegram adapter and production orchestrator. One plain-text message per shift sent to the shared group chat. Deduplication via SQLite. `--employee`, `--force`, and `--date` flags wired. Bug fixes BUG-001–004 applied. Configurable shift hours (AD-006).

Message format (from PRL):
```
Зміна: DD-MM-YYYY
{employee_name} заступає на зміну замість {prev_name}.

Наступна зміна:
DD-MM-YYYY о HH:MM — {next_name}
```
- `next_time`: driven by `shift_hours` in `schedule_mapping.json`; defaults: `17:00` (labor), `09:00` (holiday/other)
- Missing prev/next: `"-"` substituted, line not omitted

---

## Deliverables — Files Changed

| File                                     | Change                                                                                                                                        | Status  |
|------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|---------|
| `messenger/telegram_adapter.py`          | Full implementation — `send()` + `health_check()`                                                                                             | ✅       |
| `main.py`                                | `_format_message(ctx, shift_hours)`, `_shift_hours()`, `run_production()`; BUG-001/002/003/004 fixed; Telegram health check in `run_health()` | ✅       |
| `models.py`                              | `date: Optional[str] = None` added to `RunMode`                                                                                               | ✅       |
| `cli.py`                                 | `--date YYYY-MM-DD` flag added with format validation; requires `--production`                                                                | ✅       |
| `schedule_parser.py`                     | `_load_mapping` → `load_mapping` (public); `shift_hours` HH:MM validation; `_DAY_TYPE_ALIASES` for British spelling                           | ✅       |
| `data/schedule_mapping.json.example`     | `shift_hours` block added                                                                                                                     | ✅       |
| `data/schedule_mapping.json`             | `shift_hours` block added with default values — GAP-004 fix                                                                                  | ✅       |
| `tests/test_telegram_adapter.py`         | New — 6 unit tests, all mocked                                                                                                                | ✅       |
| `tests/test_format_message.py`           | New — 11 unit tests; HOURS dict param; BUG-001 regression + custom hours tests                                                                | ✅       |
| `tests/test_cli.py`                      | 3 tests added: `--date` happy path, missing `--production`, invalid format                                                                    | ✅       |
| `tests/create_fixture.py`                | `shift_hours` added to fixture mapping                                                                                                        | ✅       |
| `README.md`                              | Steps 5–9 for IT Owner; expanded CLI reference; "Coming next" updated to S004                                                                 | ✅       |
| `Backlog/2026-04-30_Development_Plan.md` | S002 → ✅ Done; S003 → ⏳ DEV complete                                                                                                          | ✅       |

---

## Implementation Notes

**`messenger/telegram_adapter.py` — REST adapter**  
`send()` POSTs to `sendMessage` endpoint; raises on HTTP error or `ok: false` API response. `health_check()` calls `getMe`; returns `False` on any failure (never raises). Timeout: 10 seconds on all requests.

**`main.py` — `_format_message(ctx, shift_hours)`**  
Pure function. Converts ISO date to `DD-MM-YYYY` for display. Looks up `next_time` from `shift_hours[day_type]`. BUG-001: `rstrip(".")` on prev name prevents double period when initials end with `.`.

**`main.py` — `_shift_hours(config)`**  
Loads `schedule_mapping.json`, merges `shift_hours` block over `_DEFAULT_SHIFT_HOURS`. IT can override per day type without touching code.

**`main.py` — `run_production(config, run_mode)`**  
BUG-003 fix: filters all_shifts to `shift_date == target_date` before processing — XLSX contains full month, cron sends only for the current date (or `--date` override). BUG-002 fix: `compute_contexts()` runs on the full date's shifts before the `--employee` filter is applied, so prev/next colleagues are resolved correctly. BUG-004: `time.sleep(1)` between sends (Telegram rate limit). Exits 0 if zero failures, exits 1 if any failure.

**`cli.py` — `--date` flag**  
Accepts `YYYY-MM-DD`; validated at parse time via `datetime.strptime`. Rejected unless `--production` is also present.

**`schedule_parser.py` — `load_mapping()`**  
Made public (removed underscore prefix) so `main.py` can call it directly for `shift_hours`. Validates all `shift_hours` values match `HH:MM` regex. Normalises British spelling `labour` → `labor`.

---

## Bug Fixes Applied

| Bug     | Description                                                               | Fix                                                   |
|---------|---------------------------------------------------------------------------|-------------------------------------------------------|
| BUG-001 | Double period for names ending with `.` (e.g. `А.С..`)                    | `raw_prev.rstrip(".")` before inserting into template |
| BUG-002 | `--employee` filter applied before `compute_contexts()` — wrong prev/next | Filter moved to after `compute_contexts()`            |
| BUG-003 | `run_production()` sent all month's shifts, not just today                | Filter `all_shifts` to `shift_date == target_date`    |
| BUG-004 | No rate limiting between Telegram sends                                   | `time.sleep(1)` after each successful send            |
| BUG-005 | "Наступна зміна" always "-" — date filter stripped tomorrow's shifts before `compute_contexts()` | `compute_contexts(all_shifts)` on full month; date filter moved to contexts (AD-001 amendment) |
| CR-003-2 | Add department title to message header line | `f"Зміна: {s.department} {date_display}\n"` — uses XLSX column header already stored in `Shift.department`, mapped via `department_columns` in `schedule_mapping.json` |

---

## Tech Debt

| #      | Description                                                                              | Severity  | Decision                                                                            |
|--------|------------------------------------------------------------------------------------------|-----------|-------------------------------------------------------------------------------------|
| TD-001 | `run_production()` orchestrator has no tests (dedup, send, record, error path) — GAP-001 | Medium    | Deferred — requires mock wiring for DB + adapter; low risk given covered unit tests |
| TD-002 | `--employee` filter behavior not covered by integration test — GAP-002                   | Low       | Deferred                                                                            |
| TD-003 | `--force` flag behavior not covered by test — GAP-003                                    | Low       | Deferred                                                                            |
| TD-004 | Date column returns integer `1` for real XLSX (day-of-month format not yet supported)    | Medium    | NTD — Owner accepted at S002 UAT                                                    |

---

## Out of Scope

- `ViberAdapter.send()` — deferred to S007 (P2)
- Group @mention per doctor — deferred to S005 (POC2)
- Personal DMs — deferred to S006

---

## Dev Workflow

```bash
docker compose build
docker compose run --rm bot python tests/create_fixture.py
docker compose run --rm bot pytest
docker compose run --rm bot python main.py                              # health check
docker compose run --rm bot python main.py --dry-run                   # preview messages
docker compose run --rm bot python main.py --production                # send for today
docker compose run --rm bot python main.py --production --date 2026-04-28  # resend past date
docker compose run --rm bot python main.py --production --employee "Alice" # resend one person
docker compose run --rm bot python main.py --production --force        # ignore dedup
```
