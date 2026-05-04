# Sprint S005 — Developer Handoff Artifact
**Date:** 2026-05-03  
**Sprint:** S005 — Webhook Infrastructure  
**Status:** 🔄 UAT IN PROGRESS — F11 fix implemented; awaiting server verification

---

## Deliverables completed

| ID  | Deliverable                          | File(s)                                          | Status |
|-----|--------------------------------------|--------------------------------------------------|--------|
| D1  | CGI webhook handler                  | `bot_hook.py`                                    | ✅ (`_handle()` reused; `main()` unused in production — see D9) |
| D2  | DB — users + conversation tables     | `db.py` (additive)                               | ✅     |
| D3  | CLI flags: --register-webhook, --bootstrap-it | `cli.py`, `models.py`                  | ✅     |
| D4  | main.py dispatch                     | `main.py`                                        | ✅     |
| D5  | .env.example additions               | `.env.example`                                   | ✅     |
| D6  | readme_WEBHOOK.md setup guide               | `readme_WEBHOOK.md`                                     | ✅     |
| D7  | Webhook routing tests (12 tests)     | `tests/test_webhook_routing.py`                  | ✅     |
| D8  | DB users/conversation tests (9 tests) | `tests/test_db_users.py`                        | ✅     |
| D9  | WSGI entry point (replaces CGI delivery) | `passenger_wsgi.py`                          | ✅ Added 2026-05-04 — F11 fix (see post-UAT fixes below) |

---

## Test results

```
113 passed in 0.70s
```

- 92 pre-existing tests: all green (zero regressions)
- 21 new tests: all green

### Post-QA fixes (found during Owner UAT)

| Fix | File | Change |
|-----|------|--------|
| F6 — symlink path resolution | `bot_hook.py:11` | `os.path.abspath` → `os.path.realpath` |
| F7 — venv package access | `bot_hook.py:12–14` | Added `_VENV` `sys.path` injection; Architect revised to use `sys.version_info` instead of hardcoded `"python3.11"` |
| F10/F11 — CGI unavailable on hosting | `passenger_wsgi.py` (new) | CGI delivery replaced with WSGI/Passenger. `passenger_wsgi.py` is the Passenger entry point; reuses `_handle()` from `bot_hook.py` unchanged. `readme_WEBHOOK.md` Step 1 rewritten. `.env.example` `WEBHOOK_URL` updated to `/Shedule_bot`. |

---

## Files changed

### New files
- `bot_hook.py` — webhook handler; `_handle()` pure function used by both CGI (unused) and WSGI entry points
- `passenger_wsgi.py` — WSGI entry point for Passenger (cPanel "Setup Python App"); added 2026-05-04 as F11 fix
- `readme_WEBHOOK.md` — setup guide (cPanel Python App → secret → register → bootstrap → verify)
- `tests/test_webhook_routing.py` — 12 tests: /start, /whoami, /help, /setrole (gating, valid, invalid, unknown target), unknown command, no-crash guards
- `tests/test_db_users.py` — 9 tests: upsert create/update/idempotency, get_user, set_user_role, conversation state CRUD + idempotency

### Modified files
- `db.py` — added `init_users_table`, `init_conversations_table`, `get_user`, `upsert_user`, `set_user_role`, `get_conversation_state`, `set_conversation_state`; extended `init_db()` to call both init functions
- `models.py` — added `bootstrap_it: Optional[str]` to `RunMode`; updated mode docstring
- `cli.py` — added `--register-webhook` and `--bootstrap-it` flags; mutual exclusion guard; mode dispatch
- `main.py` — added `run_register_webhook(config)` and `run_bootstrap_it(config, telegram_id)`; updated imports and dispatch
- `.env.example` — added `WEBHOOK_URL` and `WEBHOOK_SECRET_TOKEN` with generation instructions

---

## Architecture decisions implemented

| AD          | Decision                                                                                   |
|-------------|--------------------------------------------------------------------------------------------|
| AD-S005-001 | Webhook delivery via Passenger/WSGI — `passenger_wsgi.py` entry point; `_handle()` pure function reused unchanged |
| AD-S005-002 | `_handle` is a pure function (no CGI/WSGI deps) — fully testable without server env       |
| AD-S005-003 | 200 response returned after processing — acceptable latency for Telegram (well within 60s retry window) |
| AD-S005-004 | Secret token validated before 200 response — 403 returned to Telegram if wrong             |
| AD-S005-005 | `bot_hook.py` imports only from `db.py`; zero dependency on `main.py` — no regression risk |
| AD-S005-006 | `upsert_user` preserves role on name update — prevents accidental demotion                 |
| AD-S005-007 | `os.path.realpath(__file__)` used for `_ROOT` in `bot_hook.py` — correctly resolves path when executed via symlink (found as F6 during Owner UAT) |
| AD-S005-008 | Venv `site-packages` injected into `sys.path` at startup via `sys.version_info` — both CGI and WSGI entry points use existing venv without separate install (found as F7 during Owner UAT) |
| AD-S005-009 | CGI unavailable on this Namecheap account — confirmed by shell script test; `cgi-bin/` + `.htaccess` also return 404 |
| AD-S005-010 | WSGI/Passenger via cPanel "Setup Python App" is the supported Python deployment method; `passenger_wsgi.py` named per Passenger convention |

---

## UAT checklist (Owner)

- [ ] U005-1: Send `/start` to bot → receive welcome with Telegram ID and role `pending`
- [ ] U005-2: Send `/whoami` → receive ID, name, role
- [ ] U005-3: Send `/help` as pending user → `/setrole` NOT shown
- [ ] U005-4: Run `--bootstrap-it <your_id>` → `[BOOTSTRAP] ✅ IT user <id> registered`
- [ ] U005-5: Send `/help` as IT user → `/setrole` shown
- [ ] U005-6: Use `/setrole <other_id> staff` as IT user → `✅ Роль … оновлено: staff`
- [ ] U005-7: Attempt `/setrole` as non-IT user → `⛔ Не авторизовано.`
- [ ] U005-8: Send unknown command → reply with `/help` suggestion
- [ ] U005-9: Check `webhook.log` is written on handler error (no crash)

---

## Deployment steps

See `readme_WEBHOOK.md` for full setup.  
Quick reference: cPanel Python App (app root = `Shedule_bot`, startup file = `passenger_wsgi.py`) → set `.env` (`WEBHOOK_URL`, `WEBHOOK_SECRET_TOKEN`) → `--register-webhook` → restart app in cPanel → `--bootstrap-it`.
