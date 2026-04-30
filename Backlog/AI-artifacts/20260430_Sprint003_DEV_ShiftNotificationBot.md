# Sprint 003 — Developer Deliverables
**Sprint:** 003  
**Role:** Developer  
**Date:** 2026-04-30  
**Status:** ⏳ DEV complete — awaiting QA + Owner UAT  
**Arch ref:** [`20260405_Sprint002_ARCH_ShiftNotificationBot.md`](20260405_Sprint002_ARCH_ShiftNotificationBot.md) (S003 scope defined in Development Plan + CR-001)  
**Plan ref:** [`2026-04-30_Development_Plan.md`](../2026-04-30_Development_Plan.md)

---

## Scope

Implement Telegram adapter and production orchestrator. One plain-text message per shift sent to the shared group chat. Deduplication via SQLite. `--employee` and `--force` flags wired.

Message format (from PRL):
```
Зміна: DD-MM-YYYY
{employee_name} заступає на зміну замість {prev_name}.

Наступна зміна:
DD-MM-YYYY о HH:MM — {next_name}
```
- `next_time`: `17:00` for `labor`, `09:00` for `holiday` / `other`
- Missing prev/next: `"-"` substituted, line not omitted

---

## Deliverables — Files Changed

| File | Change | Status |
|------|--------|--------|
| `messenger/telegram_adapter.py` | Full implementation — `send()` + `health_check()` | ✅ |
| `main.py` | Added `_format_message()`, `run_production()`; wired `--employee`, `--force`; Telegram health check in `run_health()` | ✅ |
| `tests/test_telegram_adapter.py` | New — 6 unit tests, all mocked | ✅ |
| `tests/test_format_message.py` | New — 9 unit tests covering template and edge cases | ✅ |
| `README.md` | Added steps 5–9 for IT Owner; expanded CLI reference; "Coming next" updated to S004 | ✅ |
| `Backlog/2026-04-30_Development_Plan.md` | S002 → ✅ Done; S003 → ⏳ DEV complete | ✅ |

---

## Implementation Notes

**`messenger/telegram_adapter.py` — REST adapter**  
`send()` POSTs to `sendMessage` endpoint; raises on HTTP error or `ok: false` API response. `health_check()` calls `getMe`; returns `False` on any failure (never raises) — safe to call from health check without crashing. Timeout: 10 seconds on all requests.

**`main.py` — `_format_message(ctx)`**  
Pure function. Converts ISO date to `DD-MM-YYYY` for display. Determines `next_time` from `next_colleague.day_type`. Returns full Ukrainian message string. No I/O.

**`main.py` — `run_production(config, run_mode)`**  
Iterates `ShiftContext` list. Skips already-notified shifts unless `--force`. Records each send attempt (ok/fail) in SQLite regardless of outcome — failed sends are retryable on next run. Sleeps 1 second between sends (Telegram rate limit: 1 msg/sec per chat). Exits 0 if zero failures, exits 1 if any failure.

**`main.py` — `run_health()` — Telegram check added**  
Calls `TelegramAdapter.health_check()`. Adds `[TELEGRAM] ✅/❌` line to health output. Failure marks `all_ok = False`.

**`run_production` — `--employee` filter**  
Applied before `compute_contexts()` — context (prev/next) is computed only within the filtered set. If no shifts found for the named employee, exits 1 with a clear message.

**`run_production` — `--force` flag**  
Bypasses `was_notified()` check. Still records every send attempt in DB.

---

## Known Issues

| # | Description                                                                                      | Severity  | Decision                                               |
|---|--------------------------------------------------------------------------------------------------|-----------|--------------------------------------------------------|
| 1 | Double period in message when staff name ends with `.` (e.g. `"А.С."`) — output: `замість А.С..` | Minor     | NTD — fix in message formatter before S003 UAT         |
| 2 | Date column returns integer `1` for real XLSX (day-of-month format not yet supported)            | Medium    | NTD — Owner confirmed acceptable for now (UAT note #3) |

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
docker compose run --rm bot python main.py              # health check
docker compose run --rm bot python main.py --dry-run    # preview messages
docker compose run --rm bot python main.py --production # send (requires real .env)
```
