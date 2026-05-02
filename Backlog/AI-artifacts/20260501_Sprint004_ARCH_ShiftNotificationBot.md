# Sprint 004 — Architecture
**Sprint:** 004  
**Role:** Architect  
**Date:** 2026-05-01  
**Status:** ✅ APPROVED — Option A (Docker cron, local automation)  
**Scope:** Local automation via Docker cron service. Hosting deploy deferred to S004b.  
**Depends on:** S003 UAT pass  
**Blocks:** S004b (hosting deploy)

---

## Sprint Goal

The bot fires automatically on a schedule **locally via Docker**. IT runs `docker compose up -d cron` once and the bot sends shift notifications at 07:00 every morning without any manual trigger. Full end-to-end automation is verified locally before the hosting deploy sprint begins.

---

## Scope Boundaries

| In scope | Out of scope                                |
|----------|---------------------------------------------|
| `cron` service in `docker-compose.yml` using `supercronic` | Namecheap cPanel deploy (S004b)             |
| `crontab` file — configurable schedule | venv setup on hosting                       |
| Cron fires `python main.py --production` daily at 07:00 | Security hardening on server                |
| Log written per run as before | Log retention cron on server                |
| README — Local automation section | README — Production Install section (S004b) |
| Owner UAT: verify auto-fire locally | Viber adapter (S007)                        |

---

## Key Architectural Decisions

### AD-S004-001 — Docker cron service via supercronic (Owner approved Option A)

**Context:** The bot is a one-shot CLI. Automation requires an external trigger. On production hosting this will be cPanel cron. For local verification, Docker provides an equivalent cron environment.

**Decision:** Add a `cron` service to `docker-compose.yml`. It uses `supercronic` — a Docker-native, non-root cron daemon that reads a standard `crontab` file.

**Why supercronic over system crond:**
- Runs as non-root inside container
- Exits cleanly on SIGTERM (Docker-friendly)
- No `/etc/cron.d` access required
- Logs to stdout (visible via `docker compose logs cron`)

**Bot code: no changes.** The bot remains a one-shot CLI. The cron service is infrastructure only.

---

### AD-S004-002 — Schedule configuration via `crontab` file

**Decision:** A `crontab` file at the project root defines the schedule. IT edits one line to change timing. Default: daily at 07:00.

```
# crontab
# Format: minute hour day month weekday command
0 7 * * * python /app/main.py --production
```

**For local testing:** IT can temporarily set `* * * * *` (every minute) to verify the cron fires and sends. Dedup prevents duplicate sends — safe to test repeatedly.

**Cron service reads this file at startup.** Changing the schedule requires `docker compose restart cron`.

---

### AD-S004-003 — docker-compose.yml cron service

**`cron` service contract:**

```yaml
cron:
  build: .
  volumes:
    - ./data:/data
    - ./crontab:/app/crontab:ro
  env_file: .env
  command: supercronic /app/crontab
  restart: unless-stopped
```

`restart: unless-stopped` — cron service recovers automatically after Docker host reboot.

**`bot` service unchanged** — used for manual one-shot runs as before.

**`supercronic` added to `requirements.txt`:** Not a Python package — added to `Dockerfile` via `curl` download. Developer to handle install method appropriate for the base image.

---

### AD-S004-004 — Cron timing (07:00 daily)

**Decision confirmed from earlier Architect ruling:**
- Single daily fire at 07:00
- Labor shifts (17:00 start): 10h advance notice — acceptable for POC
- Holiday shifts (09:00 start): 2h advance notice — adequate
- Dedup prevents double-send if cron fires twice

**Review trigger for Option B:** If Owner finds 10h too early for labor shift notifications after one month live, S005 adds a second 15:30 cron entry to the `crontab` file. No code change required.

---

### AD-S004-005 — Dockerfile change for supercronic

`supercronic` is a compiled Go binary — not a Python package. Developer installs it in the `Dockerfile` via `curl` from the official GitHub release.

```dockerfile
# Install supercronic
RUN curl -fsSL https://github.com/aptible/supercronic/releases/download/v0.2.29/supercronic-linux-amd64 \
    -o /usr/local/bin/supercronic && chmod +x /usr/local/bin/supercronic
```

Version pinned to `v0.2.29` (latest stable at time of writing). Developer confirms version before implementing.

---

### AD-S004-006 — Stdout handling in cron context

**Decision:** No change to logging code. The bot already writes to a timestamped log file on every run. `supercronic` captures stdout/stderr and emits it to its own stdout — visible via `docker compose logs cron`. No email noise (Docker has no mail system).

---

### AD-S004-007 — Token sanitization in adapter (resolves BUG-S004-001)

**Problem:** `requests` exceptions include the full request URL in the exception message. The URL contains the bot token (`/bot{TOKEN}/sendMessage`). When `run_production()` logs the raw exception, the token is written to the log file and stored in the DB `error` column — violating S001 Security Compliance.

**Decision:** Fix at the `TelegramAdapter` boundary — the only component that knows the URL contains a token. `run_production()` must never receive a token-bearing exception string.

**`send()` contract change:**
```python
try:
    resp = requests.post(...)
    resp.raise_for_status()
except requests.exceptions.RequestException as exc:
    raise RuntimeError(f"Telegram send failed: {type(exc).__name__}") from None
```
`from None` suppresses exception chaining — the original (token-bearing) exception is not attached and cannot be logged upstream.

**`health_check()` contract change:**
```python
except Exception as exc:
    logger.warning("Telegram health check failed: %s", type(exc).__name__)
    return False
```

No changes required in `run_production()` or `record_notification()` — they will receive a clean message.

---

### AD-S004-008 — Docker DNS (resolves BUG-S004-002)

**Problem:** Both `bot` and `cron` services fail to resolve external hostnames (`api.telegram.org`) from inside Docker containers due to host DNS configuration on this machine.

**Decision:** Add `dns: [8.8.8.8, 8.8.4.4]` to both services in `docker-compose.yml`. Google public DNS bypasses host DNS configuration and is reachable from Docker bridge networks.

---

### AD-S004-009 — Cron service timezone (resolves OBS-002, superseded by AD-S004-010)

**Decision:** Add `TZ: UTC` to the `cron` service environment. Supercronic interprets cron schedule expressions using the container's local timezone. Making it explicit prevents any Docker host timezone from shifting schedule interpretation.

**Superseded by AD-S004-010** — hardcoded UTC was found to be incorrect during UAT (Owner configures times in local timezone, not UTC).

---

### AD-S004-010 — Configurable timezone via `.env` (resolves NFR-S004-001)

**Raised by:** Owner (UAT 2026-05-01) — sprint paused pending this fix.

**Problem (NFR-S004-001 — Reliability: Timezone Alignment):**  
`shift_hours` times are interpreted by `supercronic` in the container timezone. With `TZ=UTC` hardcoded, a Maintainer who sets `"labour": "17:00"` expecting 17:00 Kyiv time will get a notification at 17:00 UTC = 20:00 Kyiv — 3 hours late. No error, no warning — silent drift.

**Quality characteristic:** Reliability → Correctness of scheduled behaviour under deployment assumptions.

**Decision:**
1. Remove hardcoded `TZ=UTC` from `docker-compose.yml` cron service
2. Add `TZ=Europe/Kyiv` to `.env.example` with explanation — Maintainer sets this once at deploy
3. `docker-compose.yml` passes `TZ` from env (no hardcoded value)
4. Health check (`--health`) reports the active container timezone so Maintainer can verify alignment

**Why no hardcoded default:** A silent wrong default (UTC) is worse than a missing one. If `TZ` is unset, `supercronic` uses the Docker host timezone — visible in health check output.

**`.env.example` addition:**
```
# Timezone for cron schedule — must match the timezone where shift times are defined
# Examples: Europe/Kyiv, UTC, Europe/Warsaw
TZ=Europe/Kyiv
```

**`docker-compose.yml` cron service:**
```yaml
environment:
  - TZ   # read from .env — set to your local timezone
```

---

## Developer Deliverables

| # | Deliverable | Notes |
|---|-------------|-------|
| D1 | `crontab` file at project root | Default: `0 7 * * *`; comment explains how to test with `* * * * *` |
| D2 | `docker-compose.yml` — add `cron` service | Uses `supercronic`, mounts `./data` and `./crontab` |
| D3 | `Dockerfile` — install `supercronic` binary | Pinned version, `chmod +x` |
| D4 | README — Local Automation section | `docker compose up -d cron`, how to watch logs, how to change schedule |
| D5 | README — update message format example | Add department to "Зміна:" line per CR-003-2 |
| D6 | Verify all env-provided paths work correctly in cron container context | No relative path fallbacks |
| D7 | `docker-compose.yml` — remove hardcoded `TZ=UTC`; pass `TZ` from `.env` | AD-S004-010 |
| D8 | `.env.example` — add `TZ=Europe/Kyiv` with explanation | AD-S004-010 |
| D9 | Health check — report active container timezone + current local datetime | AD-S004-010 + 004-3 |
| D10 | README — add cron verification step (compare `[TIMEZONE]` to wall clock) | 004-3 |

---

## Module Contracts — No Changes

All module contracts from S003 ARCH remain valid. No new Python modules introduced in S004.

---

## Design Issue — DI-S004-001: Cron timing vs shift_hours (raised during UAT)

**Raised by:** Owner (UAT 2026-05-01)  
**Status:** ⏸ Open — deferred to S005

### Observation

The system currently has two places that relate to timing:
- `crontab` — when the bot fires (07:00 daily, cron syntax, read by supercronic)
- `data/schedule_mapping.json` → `shift_hours` — shift start times shown in messages

Owner's goal: single source of truth — IT edits only `schedule_mapping.json`.

### Design intent

`shift_hours` should drive cron timing directly. Labour shifts start at 17:00, holiday at 09:00 — the notification fires at those times, not at a fixed 07:00. No separate `notification_time` field is needed.

### Gap identified

Generating two cron entries (09:00 and 17:00) from `shift_hours` is technically straightforward via a startup script (`gen_crontab.py`). However, the current dedup mechanism (employee + date) does not distinguish by day type. With two cron entries firing every day:

- On a holiday day: 09:00 cron fires → sends. 17:00 cron fires → dedup blocks. ✅ correct
- On a labour day: 09:00 cron fires → sends (wrong time — labour shift is at 17:00). 17:00 cron fires → dedup blocks. ❌ wrong

**Root cause:** The bot has no awareness of current wall-clock time relative to shift type. It sends for today's date regardless of which cron triggered it.

### Resolution required (S005)

To implement this correctly, one of the following is needed:

**Option A — `--shift-type` flag (preferred):** The crontab generator produces:
```
0 9  * * *  python /app/main.py --production --shift-type holiday
0 17 * * *  python /app/main.py --production --shift-type labour
```
The bot filters to only send shifts matching the given `--shift-type` on that run. Dedup remains per employee+date+shift_type.

**Option B — time-window filter:** Bot checks whether the current time matches the shift start time from `shift_hours` (±N minutes) and skips if not. No new flag — the bot self-selects.

**Architect preliminary ruling:** Option A is cleaner and more explicit. S005 scope: `gen_crontab.py` startup script + `--shift-type` flag in `main.py` + updated dedup key.

### Current state (S004)

`crontab` remains a static file at `0 7 * * *`. IT must edit it manually if timing changes. This is acceptable for POC — the 07:00 fire gives sufficient advance notice for both shift types (2h for holiday at 09:00, 10h for labour at 17:00).

**Open question for Owner before S005 scoping:**

| # | Question |
|---|----------|
| OQ-S004-1 | Should notification fire AT shift start time (17:00 / 09:00), or before it (advance notice)? If before, how many minutes/hours in advance? |

---

## UAT Checklist — Owner Executes Locally

| # | Action | Expected result |
|---|--------|-----------------|
| U01 | `docker compose up -d cron` | Cron service starts, no errors in `docker compose logs cron` |
| U02 | Set `crontab` to `* * * * *`, restart cron service, wait 1 minute | Bot fires, message appears in Telegram group, log written in `data/logs/` |
| U03 | Check `docker compose logs cron` | Supercronic output shows bot ran, exit 0 |
| U04 | Run bot a second time within same minute | `skipped=N` — dedup working under cron |
| U05 | Restore `crontab` to `0 7 * * *`, restart cron | Schedule confirmed for daily 07:00 |
| U06 | `docker compose stop cron` then `docker compose start cron` | Service restarts cleanly, schedule resumes |
| U07 | `docker compose down` then `docker compose up -d cron` | Full restart, cron fires at next scheduled time |

---

## NFR — NFR-S004-002: `--reload-schedule` scope too broad (raised UAT 2026-05-02)

**Raised by:** Architect (UAT finding 004-05)  
**Status:** ⏸ Deferred to S005

**Problem:** `--reload-schedule` deletes dedup records for **all employees** on affected dates. If only one employee's day type was corrected in the XLSX, running `--reload-schedule` wipes the dedup for every other employee on those dates — cron or the next `--production` run resends notifications for all of them, not just the corrected one.

**Workaround (current):** Use `--production --force --employee "Name"` to target only the corrected employee without touching others' dedup.

**Proposed fix (S005):** Add `--reload-schedule --employee "Name"` scoped clear — deletes dedup only for the specified employee on dates found in the XLSX.

---

## Deferred to S004b — Hosting Deploy

| Item | Notes |
|------|-------|
| Namecheap cPanel venv setup | Needs OQ-1 (cPanel username), OQ-2 (git availability), OQ-3 (server timezone) |
| `.env` with absolute paths on server | Blocked on OQ-1 |
| cPanel cron job configuration | Same `crontab` schedule, different trigger mechanism |
| Security hardening (file permissions) | `chmod 600 .env`, `chmod 600 shift_bot.db`, `chmod 700 logs/` |
| Log retention cron on server | `find ~/logs -mtime +30 -delete` |
| README — Production Install section | Step-by-step for Namecheap |

**Open questions for Owner (S004b):**

| # | Question |
|---|----------|
| OQ-1 | cPanel username (for absolute path examples) |
| OQ-2 | Is `git` available in cPanel terminal, or upload via File Manager / FTP? |
| OQ-3 | Server timezone in cPanel (determines when "07:00 cron" fires) |

---

## Sprint Sign-off

| Role      | Name | Date       | Status |
|-----------|------|------------|--------|
| Architect | AI   | 2026-05-01 | ✅ APPROVED (amended AD-S004-010 — 2026-05-01) |
| Developer | AI   | 2026-05-01 | ⏸ D7–D9 pending |
| QA        | AI   | 2026-05-01 | ⏸ Re-verification pending D7–D9 |
| Owner     |      |            | ⏸ UAT paused — awaiting D7–D9 |
