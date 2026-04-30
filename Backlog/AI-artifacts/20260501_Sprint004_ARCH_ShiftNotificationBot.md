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

| In scope | Out of scope |
|----------|--------------|
| `cron` service in `docker-compose.yml` using `supercronic` | Namecheap cPanel deploy (S004b) |
| `crontab` file — configurable schedule | venv setup on hosting |
| Cron fires `python main.py --production` daily at 07:00 | Security hardening on server |
| Log written per run as before | Log retention cron on server |
| README — Local automation section | README — Production Install section (S004b) |
| Owner UAT: verify auto-fire locally | Viber adapter (S007) |

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

## Developer Deliverables

| # | Deliverable | Notes |
|---|-------------|-------|
| D1 | `crontab` file at project root | Default: `0 7 * * *`; comment explains how to test with `* * * * *` |
| D2 | `docker-compose.yml` — add `cron` service | Uses `supercronic`, mounts `./data` and `./crontab` |
| D3 | `Dockerfile` — install `supercronic` binary | Pinned version, `chmod +x` |
| D4 | README — Local Automation section | `docker compose up -d cron`, how to watch logs, how to change schedule |
| D5 | README — update message format example | Add department to "Зміна:" line per CR-003-2 |
| D6 | Verify all env-provided paths work correctly in cron container context | No relative path fallbacks |

---

## Module Contracts — No Changes

All module contracts from S003 ARCH remain valid. No new Python modules introduced in S004.

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
| Architect | AI   | 2026-05-01 | ✅ APPROVED |
| Developer |      |            | ⏸ Ready to start |
| QA        |      |            | ⏸ |
| Owner     |      |            | ⏸ |
