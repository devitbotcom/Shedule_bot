# Sprint 003 — Architecture
**Sprint:** 003  
**Role:** Architect  
**Date:** 2026-04-30  
**Status:** ✅ APPROVED (includes BUG-003 and BUG-004 decisions)  
**Scope:** Telegram adapter + production orchestrator — group chat, plain text (POC)  
**Depends on:** S002 ARCH + CR-001 + Development Plan  
**Blocks:** S004

---

## Sprint Goal

Deliver `--production` mode. The Owner runs one command and all duty doctors for **today's shift** receive a correctly formatted Telegram message in the shared group chat. Deduplication prevents resends. Cron-safe.

---

## Scope Boundaries

| In scope                                                               | Out of scope                     |
|------------------------------------------------------------------------|----------------------------------|
| `TelegramAdapter.send()` — REST call to Telegram API                   | Viber adapter (S007)             |
| `TelegramAdapter.health_check()` — `getMe` verification                | Group @mention per doctor (S005) |
| `_format_message()` — Ukrainian message template                       | Personal DMs (S006)              |
| `run_production()` — orchestrator: filter by date, dedup, send, record | Multi-ward (S008)                |
| `run_health()` — Telegram check added                                  | Receipt/confirmation tracking    |
| `--date YYYY-MM-DD` CLI flag — optional date override                  |                                  |
| Date filter: today only by default                                     |                                  |
| Rate limiting: 1-second sleep between sends                            |                                  |

---

## Key Architectural Decisions

### AD-001 — Date filter in `run_production()` (resolves BUG-003)

**Problem:** `parse_schedule()` returns all shifts from the full month XLSX. Without filtering, `--production` sends all month's notifications at once.

**Decision:** `run_production()` filters shifts to `shift_date == today` before sending. The server date at execution time is used. Deduplication remains as the secondary guard against double-sends if cron fires twice.

**CLI override:** `--date YYYY-MM-DD` added as optional flag. If omitted, defaults to today. Allows IT to manually trigger for a specific date (e.g. after a failed cron run on a past date).

**Interaction with `--reload-schedule`:** Unchanged — clears dedup for all dates in the XLSX. After reload, next `--production` run sends for today only.

---

### AD-002 — Telegram rate limiting (resolves BUG-004)

**Problem:** Sending N messages in rapid succession to the same group chat risks hitting Telegram's 1 message/second per chat limit.

**Decision:** `time.sleep(1)` enforced after each successful send in `run_production()`. No configurable delay for POC — staff volume is small (≤30 shifts per run = ≤30 seconds total runtime). This is acceptable for a cron job.

**Added to Quality table:** Performance — Telegram rate limit.

---

### AD-003 — Message template (from PRL + Development Plan)

```
Зміна: DD-MM-YYYY
{employee_name} заступає на зміну замість {prev_name}.

Наступна зміна:
DD-MM-YYYY о HH:MM — {next_name}
```

- `{prev_name}` / `{next_name}`: employee name or `-` if none — line not omitted
- `next_time`: read from `shift_hours` in `schedule_mapping.json` (see AD-006)
- Date display: `DD-MM-YYYY`; internal storage: `YYYY-MM-DD`
- **Double period guard:** if `prev_name` ends with `.`, no additional `.` appended to the line

---

### AD-006 — Shift hours configurable via `schedule_mapping.json`

**Problem:** Shift start times (`17:00` for labor, `09:00` for holiday/other) are hardcoded in `_format_message()`. IT cannot adjust them without a code change.

**Decision:** Add optional `shift_hours` block to `schedule_mapping.json`:

```json
"shift_hours": {
  "labor":   "17:00",
  "holiday": "09:00",
  "other":   "09:00"
}
```

If the key is absent, the same values are used as built-in defaults — existing mapping files require no change.

`load_mapping()` validates each present value matches `HH:MM` format and exits 1 with a clear message if invalid.

`_format_message(ctx, shift_hours)` receives the dict and looks up `shift_hours[next.day_type]`. Falls back to `"09:00"` for any unknown day_type.

**Scope of change:**
- `schedule_parser.py`: rename `_load_mapping` → `load_mapping` (public); add `shift_hours` validation
- `data/schedule_mapping.json.example`: add `shift_hours` block
- `data/schedule_mapping.json`: add `shift_hours` block with default values (IT-visible config)
- `main.py`: call `load_mapping()` at startup; pass `shift_hours` to `_format_message()`
- `tests/create_fixture.py`: include `shift_hours` in fixture mapping
- `tests/test_format_message.py`: pass `shift_hours` to all calls

---

### AD-004 — `--employee` filter scope

`--employee` restricts **which messages are sent**, not how prev/next is computed. `compute_contexts()` runs on the full today's shifts; the employee filter is applied after to select which contexts to send.

---

### AD-005 — `run_health()` — Telegram check

`TelegramAdapter.health_check()` (`getMe`) added to health check sequence. Returns `[TELEGRAM] ✅/❌`. 
Failure sets `all_ok = False` → exit 1. Requires a real token — placeholder token will show `[TELEGRAM] ❌`.

---

## CLI Changes

| Flag                | Type     | Default  | Description                    |
|---------------------|----------|----------|--------------------------------|
| `--date YYYY-MM-DD` | optional | today    | Date to send notifications for |

`RunMode.date` field added (type `str`, ISO format).

---

## Quality Acceptance — Additions

| Characteristic         | Sub-characteristic | Acceptance criterion                                                                                     |
|------------------------|--------------------|----------------------------------------------------------------------------------------------------------|
| Performance efficiency | Rate compliance    | No more than 1 message/second sent to Telegram group. Enforced by `time.sleep(1)` in `run_production()`. |
| Reliability            | Fault tolerance    | Failed send recorded in DB as `status='fail'`; run continues; exit 1 at end if any failure.              |
| Reliability            | Recoverability     | Re-running `--production` for the same date retries only failed/unsent shifts (dedup).                   |

---

## Module Contracts

### `TelegramAdapter(token: str)`
- `send(contact_id, message)` — raises on any failure (HTTP error or `ok: false`)
- `health_check()` — returns `bool`, never raises

### `run_production(config, run_mode)`
- Filters to `run_mode.date` (default: today)
- Applies `--employee` filter after `compute_contexts()`
- Bypasses dedup if `run_mode.force`
- Exits 0 if `failed == 0`, exits 1 otherwise

### `_format_message(ctx: ShiftContext, shift_hours: dict) -> str`
- Pure function — no I/O
- Handles missing prev/next with `-`
- No double period on names ending in `.`
- `shift_hours` dict keyed by day_type; fallback `"09:00"` for unknown types (see AD-006)
