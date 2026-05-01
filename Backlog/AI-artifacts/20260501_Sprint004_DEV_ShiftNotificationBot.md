# Sprint 004 — Developer Deliverables
**Sprint:** 004  
**Role:** Developer  
**Date:** 2026-05-01  
**Status:** ✅ DEV complete (incl. QA bug fixes) — awaiting QA re-verification + Owner UAT  
**Arch ref:** [`20260501_Sprint004_ARCH_ShiftNotificationBot.md`](20260501_Sprint004_ARCH_ShiftNotificationBot.md)

---

## Scope

Add Docker cron service (`supercronic`) so the bot fires automatically at 07:00 daily without manual intervention. Post-QA fixes: token sanitization in adapter (AD-S004-007), Docker DNS (AD-S004-008), cron timezone (AD-S004-009).

---

## Deliverables — Files Changed

| File | Change | Status |
|------|--------|--------|
| `Dockerfile` | Install `supercronic` v0.2.29 binary via `curl` | ✅ |
| `docker-compose.yml` | Add `cron` service; DNS fix (AD-S004-008); TZ=UTC (AD-S004-009) | ✅ |
| `crontab` | New file at project root — default `0 7 * * *`; test instructions in comments | ✅ |
| `README.md` | Add section 10 (Local Automation); fix message format example (add department per CR-003-2); update "Coming next" to S004b | ✅ |
| `messenger/telegram_adapter.py` | Token sanitization in `send()` and `health_check()` — AD-S004-007 / BUG-S004-001 | ✅ |
| `tests/test_telegram_adapter.py` | Fix existing HTTP error test; add 2 regression tests for BUG-S004-001 | ✅ |

---

## Implementation Notes

**`Dockerfile` — supercronic install**  
`curl` and `ca-certificates` installed, binary downloaded to `/usr/local/bin/supercronic`, `curl` purged and apt cache cleared — image size kept minimal. Version pinned to `v0.2.29`.

**`cron` service**  
Shares the same image and volumes as `bot` service. Mounts `.:/app` (code) and `./data:/data` (IT files). Runs `supercronic /app/crontab` as its entrypoint. `restart: unless-stopped` ensures it recovers after Docker host reboot.

**`crontab` file**  
Picked up automatically by the `cron` service via the `.:/app` volume mount — no separate bind mount needed. IT edits this file and runs `docker compose restart cron` to apply. Comments explain test mode (`* * * * *`) and dedup safety.

**Path verification (D6)**  
All env-provided paths (`/data/schedule.xlsx`, `/data/shift_bot.db`, `/data/logs`) are absolute and resolve correctly inside the `cron` container — same `/data` volume mount as `bot` service. No relative path fallbacks in code.

---

## Post-QA Fixes (QA pass 1 → ❌ FAIL)

### Fix 1 — AD-S004-007: Token sanitization (`messenger/telegram_adapter.py`)

**Resolves:** BUG-S004-001 (token in logs)

`send()` now catches `requests.exceptions.RequestException` and re-raises a sanitized `RuntimeError` using `from None` to suppress exception chaining. The raw exception (which contains the URL with token) is never propagated upstream.

`health_check()` logs only `type(exc).__name__` — never the raw exception string.

```python
except requests.exceptions.RequestException as exc:
    raise RuntimeError(f"Telegram send failed: {type(exc).__name__}") from None
```

### Fix 2 — AD-S004-008: Docker DNS (`docker-compose.yml`)

**Resolves:** BUG-S004-002 (container cannot reach `api.telegram.org`)

Added `dns: [8.8.8.8, 8.8.4.4]` to both `bot` and `cron` services. Google public DNS bypasses host DNS configuration and is reachable from Docker bridge networks.

### Fix 3 — AD-S004-009: Cron timezone (`docker-compose.yml`)

**Resolves:** OBS-002 (cron schedule timezone ambiguous)

Added `TZ: UTC` to `cron` service environment. `supercronic` uses container local timezone to interpret the crontab schedule — making it explicit prevents host timezone from shifting the 07:00 fire time.

### Tests added (`tests/test_telegram_adapter.py`)

- Fixed `test_send_raises_on_http_error` — now correctly uses `requests.exceptions.HTTPError` (a `RequestException` subclass) and asserts `RuntimeError` with "Telegram send failed"
- Added `test_send_raises_on_connection_error` — verifies token not in exception message
- Added `test_send_token_not_in_exception` — BUG-S004-001 regression guard: "SECRET_TOKEN" must not appear in raised `RuntimeError`

**Test suite: 65/65 pass (2 new tests added)**

---

## Dev Workflow

```bash
# Build image (includes supercronic)
docker compose build

# Start cron service in background
docker compose up -d cron

# Watch cron logs
docker compose logs -f cron

# Test: fire every minute (edit crontab, then restart)
docker compose restart cron

# Manual one-shot run (unchanged)
docker compose run --rm bot python main.py --production

# Stop cron
docker compose stop cron
```
