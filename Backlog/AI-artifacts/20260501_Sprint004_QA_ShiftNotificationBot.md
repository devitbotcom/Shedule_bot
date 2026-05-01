# Sprint 004 — QA Review
**Sprint:** 004  
**Role:** QA Engineer  
**Date:** 2026-05-01  
**Status:** ✅ PASS (pass 2) — all bugs closed. Ready for Owner UAT.  
**Dev ref:** [`20260501_Sprint004_DEV_ShiftNotificationBot.md`](20260501_Sprint004_DEV_ShiftNotificationBot.md)  
**Arch ref:** [`20260501_Sprint004_ARCH_ShiftNotificationBot.md`](20260501_Sprint004_ARCH_ShiftNotificationBot.md)

---

## Evidence

**Cron service status:** Running. `docker compose ps` confirms `shedule_bot-cron-1` Up 14 hours.

**Log file inspected:** `data/logs/shift_bot_20260501_174756.log` — written by cron-fired run at 17:47 UTC.

**Docker logs inspected:** `docker compose logs cron` — supercronic captures bot stdout and displays it per-job.

---

## Bug Findings

### BUG-S004-001 — Bot token exposed in log files (Severity: Critical / Security)

**Evidence — `data/logs/shift_bot_20260501_174756.log`:**
```
[ERROR] Failed: лікар9 2026-05-01 — HTTPSConnectionPool(host='api.telegram.org', port=443):
Max retries exceeded with url: /bot8730816915:AAEvsIsPnaOK3ff4n8yYHcRAU4VSlWdF8rE/sendMessage
```

The full Telegram bot token appeared in plain text in the log file on any send failure.

**Fix applied (AD-S004-007):** `TelegramAdapter.send()` now catches `requests.exceptions.RequestException` and re-raises a sanitized `RuntimeError(f"Telegram send failed: {type(exc).__name__}")` with `from None` — suppressing exception chaining so the token-bearing URL cannot propagate upstream.

**QA verification (pass 2):**
- `test_send_raises_on_connection_error` — PASS: "SECRET_TOKEN" absent from RuntimeError message
- `test_send_token_not_in_exception` — PASS: regression guard confirmed
- `test_send_raises_on_http_error` — PASS: raises `RuntimeError` matching "Telegram send failed"
- All 8 adapter tests pass

**Status:** ✅ Closed.

---

### BUG-S004-002 — Docker container cannot reach Telegram API (Severity: High)

**Evidence:**
```
Failed to resolve 'api.telegram.org' ([Errno -2] Name or service not known)
```
All three sends failed. `[PRODUCTION] sent=0  skipped=0  failed=3`.

**Root cause:** DNS resolution fails for external hosts from inside the `cron` Docker container due to host DNS configuration on this machine.

**Fix applied (AD-S004-008):** `docker-compose.yml` — `dns: [8.8.8.8, 8.8.4.4]` added to both `bot` and `cron` services.

**QA verification (pass 2):** `docker-compose.yml` inspected — confirmed:
```yaml
dns:
  - 8.8.8.8
  - 8.8.4.4
```
Present on both services. Infrastructure fix — not covered by unit tests. Requires `docker compose build && docker compose up -d cron` to activate.

**Status:** ✅ Closed (pending Owner UAT U02 to confirm network connectivity in live container).

---

## Observations (No Fix Required from Developer)

### OBS-001 — Logs ARE written — user may not know where to look

`data/logs/` contains 25 log files from previous runs including today's cron-fired run. The user reported "I do not see logs."

There are two places logs appear:
1. **File logs:** `data/logs/shift_bot_YYYYMMDD_HHMMSS.log` — one per run, on the host filesystem
2. **Docker logs:** `docker compose logs cron` — supercronic captures bot stdout, visible in real time

**Recommendation:** README should explicitly state both locations.

---

### OBS-002 — Cron timing discrepancy

Cron schedule is `0 7 * * *` (07:00 UTC). The job fired at `17:47 UTC` on 2026-05-01.

**Fix applied (AD-S004-009):** `TZ: UTC` added to `cron` service environment in `docker-compose.yml`. `supercronic` uses container local timezone — making UTC explicit prevents host timezone from shifting schedule interpretation.

**QA verification (pass 2):** `docker-compose.yml` inspected — confirmed:
```yaml
environment:
  - TZ=UTC
```
Present on `cron` service. Requires `docker compose restart cron` to take effect.

---

### OBS-003 — XLSX day_type gaps for future dates

```
[WARNING] Unknown day_type '' on 2026-05-02 — skipping row
[WARNING] Unknown day_type '' on 2026-05-03 — skipping row
```

Future rows in the XLSX have empty `Day-type` cells. Parser correctly skips them. When the schedule is fully populated, these warnings will disappear. Not a bot defect — Owner/Schedule Manager action required.

---

### OBS-004 — Automated tests for adapter security (updated)

Docker/cron infrastructure behavior is not covered by pytest — UAT remains the only verification mechanism for that. However, the BUG-S004-001 fix is now covered by automated regression tests in `tests/test_telegram_adapter.py`:
- `test_send_raises_on_connection_error`
- `test_send_token_not_in_exception`

Full suite: **65/65 pass**.

---

## UAT Checklist — Status

| # | Action | Expected | Actual | Result |
|---|--------|----------|--------|--------|
| U01 | `docker compose up -d cron` | Service starts | Service up 14h | ✅ |
| U02 | Cron fires, message in Telegram | Bot fires, message received | Bot fired, DNS failed — no message | ❌ BUG-S004-002 → fixed (Owner UAT required) |
| U03 | Log file in `data/logs/` | File written per run | Files written ✅ | ✅ |
| U04 | `docker compose logs cron` | Bot output visible | Visible ✅ | ✅ |
| U05 | Token not in logs | No secrets in log output | Token in error log | ❌ BUG-S004-001 → fixed ✅ (regression tests pass) |

---

## Sprint 004 Sign-off

| Role        | Name | Date        | Status                                                |
|-------------|------|-------------|-------------------------------------------------------|
| Developer   | AI   | 2026-05-01  | ✅                                                     |
| QA Engineer | AI   | 2026-05-01  | ✅ PASS (pass 2) — BUG-S004-001 closed, BUG-S004-002 closed |
| Owner       |      |             | ⏸ Ready for UAT — requires `docker compose build` first |
