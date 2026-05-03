# Sprint S005 — Developer Handoff Artifact
**Date:** 2026-05-03  
**Sprint:** S005 — Webhook Infrastructure  
**Status:** ✅ IMPLEMENTATION COMPLETE — ready for QA / Owner UAT

---

## Deliverables completed

| ID  | Deliverable                          | File(s)                                          | Status |
|-----|--------------------------------------|--------------------------------------------------|--------|
| D1  | CGI webhook handler                  | `bot_hook.py`                                    | ✅     |
| D2  | DB — users + conversation tables     | `db.py` (additive)                               | ✅     |
| D3  | CLI flags: --register-webhook, --bootstrap-it | `cli.py`, `models.py`                  | ✅     |
| D4  | main.py dispatch                     | `main.py`                                        | ✅     |
| D5  | .env.example additions               | `.env.example`                                   | ✅     |
| D6  | readme_WEBHOOK.md setup guide               | `readme_WEBHOOK.md`                                     | ✅     |
| D7  | Webhook routing tests (12 tests)     | `tests/test_webhook_routing.py`                  | ✅     |
| D8  | DB users/conversation tests (9 tests) | `tests/test_db_users.py`                        | ✅     |

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

---

## Files changed

### New files
- `bot_hook.py` — CGI entry point; symlinked from `public_html/`
- `readme_WEBHOOK.md` — 7-step setup guide (install deps → symlink → secret → register → bootstrap → verify)
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
| AD-S005-001 | CGI webhook — no persistent process; compatible with cPanel shared hosting                 |
| AD-S005-002 | `_handle` is a pure function (no CGI deps) — fully testable without CGI env                |
| AD-S005-003 | 200 response written immediately before processing — Telegram stops retrying               |
| AD-S005-004 | Secret token validated before 200 response — 403 returned to Telegram if wrong             |
| AD-S005-005 | `bot_hook.py` imports only from `db.py`; zero dependency on `main.py` — no regression risk |
| AD-S005-006 | `upsert_user` preserves role on name update — prevents accidental demotion                 |
| AD-S005-007 | `os.path.realpath(__file__)` used for `_ROOT` — correctly resolves path when executed via symlink from `public_html/` (found as F6 during Owner UAT) |
| AD-S005-008 | Venv `site-packages` injected into `sys.path` at startup via `sys.version_info` — CGI base Python accesses venv packages without separate `--user` install (found as F7 during Owner UAT) |

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

See `readme_WEBHOOK.md` for the full 7-step setup.  
Quick reference: symlink → chmod 755 → set `.env` → `--register-webhook` → `--bootstrap-it`.
