# Sprint 005 — Architecture

**Sprint:** 005
**Role:** Architect
**Date:** 2026-05-03
**Status:** ✅ READY FOR DEVELOPER
**Depends on:** S001–S004b complete
**Blocks:** S006 (schedule generation), S007 (Head dialogue)

---

## Sprint Goal

Bot receives Telegram messages via webhook on cPanel. IT can assign roles. Users can register and query their role. POC1 notification pipeline is untouched.

---

## Scope

| In | Out |
|---|---|
| Telegram webhook endpoint (CGI on cPanel) | Polling / getUpdates loop |
| One-time webhook registration command | Any schedule generation |
| Role system: `it` / `head` / `staff` / `pending` | Any send-notification changes |
| Commands: `/start`, `/help`, `/whoami`, `/setrole` | Viber |
| DB: `users` + `conversations` tables | Changes to `main.py`, `cli.py`, existing cron |
| Webhook secret token validation | — |
| `WEBHOOK.md` — setup instructions | — |

---

## Key Architectural Decisions

### AD-S005-001 — Webhook delivery: no persistent process

> ⚠️ **Superseded (2026-05-04):** CGI delivery model is invalid for this hosting — see AD-S005-009, AD-S005-010, and F11 (QA report). Delivery mechanism changed to WSGI/Passenger. The core architectural claim (no persistent process managed by the bot) is superseded — Passenger is a persistent process managed by cPanel, not by the bot.

Telegram sends a POST to `https://<domain>/Shedule_bot` on every inbound message. The WSGI application (`passenger_wsgi.py`) reads the JSON body, calls `_handle()`, and returns HTTP 200. Passenger (managed by cPanel) handles the process lifecycle.

**Zero regression guarantee:** `_handle()` in `bot_hook.py` is unchanged. No imports from `main.py`. No changes to any existing file except `db.py` (additive only).

---

### AD-S005-002 — Webhook secret token

`setWebhook` is called once with a `secret_token` parameter. Telegram attaches it as `X-Telegram-Bot-Api-Secret-Token` header on every POST. `bot_hook.py` validates the header before processing — rejects anything without it (returns HTTP 403).

Token stored in `.env` as `WEBHOOK_SECRET_TOKEN`. IT generates a random string (e.g. `openssl rand -hex 32`).

---

### AD-S005-003 — Role system

Four roles stored in `users` table:

| Role | Who | Capabilities in S005 |
|---|---|---|
| `pending` | Any new user | `/start`, `/whoami` |
| `staff` | Duty doctor | `/start`, `/whoami` |
| `head` | Department head | `/start`, `/whoami` (commands added in S007) |
| `it` | System owner | All of the above + `/setrole` |

First user to `/start` gets role `pending`. IT promotes via `/setrole <telegram_id> <role>`. IT role is bootstrapped: first entry in `users` table with role `it` is inserted by IT manually (or via `--bootstrap-it` CLI flag in `main.py`).

---

### AD-S005-004 — DB schema additions (additive only)

Two new tables added to existing `shift_bot.db` via new functions in `db.py`:

```sql
CREATE TABLE IF NOT EXISTS users (
    telegram_id TEXT PRIMARY KEY,
    full_name   TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'pending',
    registered_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    telegram_id  TEXT PRIMARY KEY,
    state        TEXT NOT NULL DEFAULT 'idle',
    context_json TEXT NOT NULL DEFAULT '{}',
    updated_at   TEXT NOT NULL
);
```

`init_db()` in `db.py` extended to call both new `CREATE TABLE IF NOT EXISTS` statements — idempotent, safe to run on existing DB.

---

### AD-S005-005 — Command routing

`bot_hook.py` dispatcher:

```
POST received → validate secret token → parse update JSON
→ extract message.text + from.id + from.full_name
→ upsert user in DB (register if new, update full_name)
→ match command prefix → dispatch to handler
→ send reply via Telegram sendMessage
→ exit
```

Non-command messages in S005: reply "Unknown command. Send /help."
Errors: catch all exceptions, send "⚠️ Internal error" to user, log to file, exit 0 (Telegram requires 200 response to stop retries).

---

### AD-S005-007 — Symlink-safe `_ROOT` resolution

`bot_hook.py` uses `os.path.realpath(__file__)` (not `os.path.abspath`) to resolve `_ROOT`. When the CGI file is executed via a symlink from `public_html/`, `abspath` would resolve to the symlink's directory (`~/public_html/`), making all relative imports fail. `realpath` follows the symlink to the actual source file location (`~/Shedule_bot/`).

**Rule:** any script that may be symlinked and needs sibling imports must use `realpath`.

---

### AD-S005-008 — Venv package availability for CGI

The CGI shebang (`#!/opt/alt/python311/bin/python3.11`) uses the base system Python, which cannot see the project venv. Rather than requiring a separate `--user` install (two package sets to keep in sync), `bot_hook.py` injects the venv `site-packages` directory into `sys.path` at startup:

```python
_VENV = os.path.join(_ROOT, "venv", "lib",
                     f"python{sys.version_info.major}.{sys.version_info.minor}",
                     "site-packages")
if os.path.isdir(_VENV):
    sys.path.insert(0, _VENV)
```

The version string is derived from the running interpreter (`sys.version_info`) — not hardcoded — so it remains correct if the Python minor version changes. The `isdir` guard is intentionally permissive: if the venv is absent the script proceeds and fails at the first missing import, producing a diagnosable error rather than silent misbehaviour.

---

### AD-S005-009 — CGI not available on this hosting (LiteSpeed constraint)

**Date added:** 2026-05-04 — discovered during Owner UAT (F10, F11).

> ⚠️ **Updated (2026-05-04):** Initial finding (F10) identified `public_html/` as wrong; `cgi-bin/` was attempted as fix. Further testing (F11) confirmed CGI is disabled server-wide — a plain bash script in `cgi-bin/` with `.htaccess` `Options +ExecCGI` also returned 404. CGI is entirely unavailable on this Namecheap account. See AD-S005-010 for the replacement approach.

On this Namecheap shared hosting account with LiteSpeed Web Server, CGI script execution is not available from any directory (`public_html/`, `cgi-bin/`, with or without `.htaccess` directives). The platform-supported method for running Python web code is WSGI/Passenger via cPanel "Setup Python App".

---

### AD-S005-010 — Replace CGI with WSGI/Passenger

**Date added:** 2026-05-04 — replaces CGI delivery model (AD-S005-001, AD-S005-009, F11).

Namecheap cPanel offers "Setup Python App" which deploys Python via Passenger (WSGI). An existing app is already configured at `https://digital-muzzle.com/Shedule_bot` with app root `/home/itbomenf/Shedule_bot` and Python 3.11.15.

**New file: `passenger_wsgi.py`** — WSGI entry point placed in `Shedule_bot/`. Passenger loads this file on startup.

Responsibilities:
- Inject existing `venv/` site-packages into `sys.path` (same pattern as `bot_hook.py`)
- Load `.env`
- Implement `application(environ, start_response)` — the WSGI callable Passenger invokes per request
- Validate `HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN` from `environ`
- Read POST body from `environ['wsgi.input']`
- Call `_handle()` from `bot_hook.py` — **no changes to `_handle()` required**
- Return HTTP 200 `{}`; return HTTP 403 on wrong secret

**`bot_hook.main()`:** becomes unused for production. Kept for local testing. No removal required.

**`WEBHOOK_URL`:** `https://digital-muzzle.com/Shedule_bot`

**Venv:** existing `Shedule_bot/venv/` injected via `sys.path` — no separate cPanel pip install required.

**Scope of impact:** new file `passenger_wsgi.py`; `readme_WEBHOOK.md` Step 1 rewritten; `.env.example` `WEBHOOK_URL` updated; UAT prerequisites updated. No logic changes to existing Python files.

---

### AD-S005-006 — Webhook registration

New CLI flag `--register-webhook` added to `main.py` / `cli.py`. Calls Telegram `setWebhook` with `url` + `secret_token`. Run once by IT after deployment. Idempotent.

```bash
cd ~/Shedule_bot && source venv/bin/activate && python main.py --register-webhook
```

`.env` requires two new variables:
```
WEBHOOK_URL=https://<domain>/cgi-bin/bot_hook.py
WEBHOOK_SECRET_TOKEN=<random-hex>
```

---

## Developer Deliverables

| # | Deliverable | Notes |
|---|---|---|
| D1 | `bot_hook.py` — CGI webhook handler | Secret token validation, command dispatch, error handling |
| D2 | `db.py` — `init_users_table()`, `init_conversations_table()`, `get_user()`, `upsert_user()`, `set_user_role()`, `get_conversation_state()`, `set_conversation_state()` | Additive only — no changes to existing functions |
| D3 | `main.py` + `cli.py` — `--register-webhook` flag and `run_register_webhook()` | Calls setWebhook; prints confirmation |
| D4 | `main.py` + `cli.py` — `--bootstrap-it <telegram_id>` flag | Inserts first IT user into DB |
| D5 | `.env.example` — `WEBHOOK_URL`, `WEBHOOK_SECRET_TOKEN` entries | |
| D6 | `WEBHOOK.md` — setup: place file, set permissions, register webhook, bootstrap IT | |
| D7 | `tests/test_webhook_routing.py` — command dispatch, role gating, unknown command, invalid secret | |
| D8 | `tests/test_db_users.py` — upsert, role assignment, conversation state | |

---

## UAT Checklist

| # | Action | Expected |
|---|---|---|
| U01 | IT places `bot_hook.py`, runs `--register-webhook` | `[WEBHOOK] ✅ registered: https://...` |
| U02 | IT runs `--bootstrap-it <id>` | IT user present in DB with role `it` |
| U03 | Any user sends `/start` | Welcome message received; user appears in DB as `pending` |
| U04 | IT sends `/setrole <id> head` | Role updated; user receives confirmation |
| U05 | Head sends `/whoami` | `Your role: head` |
| U06 | Non-IT sends `/setrole ...` | `⛔ Not authorised` |
| U07 | POC1 cron fires at scheduled time | Shift notifications sent normally; no regression |
| U08 | Request with wrong secret token | No response to sender; HTTP 403 returned to Telegram |

---

## Open Questions

| # | Question | Needed for | Status |
|---|---|---|---|
| OQ-1 | Server domain/path for `WEBHOOK_URL` | D3, D6 | IT to confirm |
| OQ-2 | Does `public_html/bot_hook.py` need `.htaccess` config to execute as CGI on this server? | D1 | ✅ Resolved 2026-05-04: `public_html/` does not execute CGI on LiteSpeed. Use `cgi-bin/` — no `.htaccess` required. See AD-S005-009. |

---

## Sprint Sign-off

| Role | Date | Status |
|---|---|---|
| Architect | 2026-05-03 | ✅ Ready for Developer |
| Developer | — | ⏸ |
| QA | — | ⏸ |
| Owner | — | ⏸ |
