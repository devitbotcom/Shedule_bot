# Sprint S005 — QA Delivery Report
**Date:** 2026-05-03  
**Role:** QA  
**Sprint:** S005 — Webhook Infrastructure  
**Scope:** 21 new tests across 2 new files; 6 modified/new source files  
**Suite status:** 113/113 passing (92 pre-existing + 21 new)

---

## Legend

### Design techniques

| Term                              | Meaning                                                                                                                                           |
|-----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **EP** — Equivalence Partitioning | Input space divided into partitions where all values behave the same. One representative per partition tested.                                    |
| **State-based**                   | Verifies system state before and after an operation (e.g. DB record written). Outcome checked by inspecting stored state, not just return value.  |
| **Negative**                      | Provides invalid or forbidden input and verifies the system rejects it correctly.                                                                 |
| **Contract**                      | Verifies a non-functional guarantee: no crash, no mutation, no exception propagated. The *what* is less important than the *how*.                 |
| **Regression**                    | Written specifically to prevent a known past bug or design invariant from regressing.                                                             |
| **Idempotency**                   | Verifies that running the same operation twice produces the same result as once — no corruption, duplication, or error on repeat.                 |
| **Role-gate**                     | Variant of Negative focused on authorisation: verifies that a privilege-restricted action is rejected for an under-privileged caller.             |

### Redundant / inefficient column

| Symbol            | Meaning                                                                                  |
|-------------------|------------------------------------------------------------------------------------------|
| ✅                 | Clean — no overlap, no waste                                                             |
| ⚠️ Overlaps with  | Re-asserts something already covered by another test. May still be kept for readability. |
| ⚠️ Weak assertion | Test passes when it should not, due to an overly broad condition.                        |

---

## Coverage by file

| File                            | Tests  | Notes                                                    |
|---------------------------------|--------|----------------------------------------------------------|
| `tests/test_webhook_routing.py` | 12     | Command dispatch, role gating, no-crash guards           |
| `tests/test_db_users.py`        | 9      | upsert, get_user, set_user_role, conversation state CRUD |

---

## Test table — test_webhook_routing.py

| #  | Test                                          | Main purpose                                     | Design technique         | Redundant / inefficient           |
|----|-----------------------------------------------|--------------------------------------------------|--------------------------|-----------------------------------|
| 1  | `test_start_registers_new_user_and_replies`   | `/start` creates user; reply contains ID + role  | State-based, EP          | ✅                                 |
| 2  | `test_start_preserves_existing_role`          | `/start` on known user keeps elevated role       | State-based, Regression  | ✅                                 |
| 3  | `test_whoami_returns_id_name_role`            | `/whoami` returns all three fields               | EP                       | ⚠️ Overlaps with #1 (role shown)  |
| 4  | `test_help_pending_user_no_setrole`           | Non-IT help omits `/setrole`                     | Negative, EP             | ✅                                 |
| 5  | `test_help_it_user_includes_setrole`          | IT help includes `/setrole`                      | EP                       | ✅                                 |
| 6  | `test_setrole_denied_for_pending`             | Non-IT user gets `⛔`                             | Negative, Role-gate      | ✅                                 |
| 7  | `test_setrole_sets_role_as_it`                | IT user can promote; DB updated                  | State-based              | ✅                                 |
| 8  | `test_setrole_invalid_role_shows_usage`       | Invalid role name shows usage hint               | Negative                 | ⚠️ Weak assertion (see F2)        |
| 9  | `test_setrole_unknown_target_warns`           | `/setrole` on non-existent user gives `⚠️`       | Negative                 | ✅                                 |
| 10 | `test_unknown_command_suggests_help`          | Unrecognised command suggests `/help`            | EP                       | ✅                                 |
| 11 | `test_handle_ignores_update_without_message`  | Empty update → no send, no crash                 | Contract                 | ✅                                 |
| 12 | `test_handle_ignores_message_without_from`    | Message without `from` → no send                 | Contract                 | ✅                                 |

## Test table — test_db_users.py

| #  | Test                                                    | Main purpose                               | Design technique        | Redundant / inefficient |
|----|---------------------------------------------------------|--------------------------------------------|-------------------------|-------------------------|
| 13 | `test_upsert_creates_user_with_pending_role`            | New user created with `pending` role       | State-based, EP         | ✅                       |
| 14 | `test_upsert_updates_name_preserves_role`               | Name update does not clobber role          | State-based, Regression | ✅                       |
| 15 | `test_upsert_idempotent_same_data`                      | Double upsert is stable                    | Idempotency             | ✅                       |
| 16 | `test_get_user_returns_none_for_unknown`                | Missing user returns None                  | Negative                | ✅                       |
| 17 | `test_set_user_role_returns_true_on_success`            | Role set returns True + DB updated         | State-based             | ✅                       |
| 18 | `test_set_user_role_returns_false_for_unknown`          | Non-existent user returns False            | Negative                | ✅                       |
| 19 | `test_get_conversation_state_returns_idle_for_new_user` | Default state is `idle` with empty context | EP                      | ✅                       |
| 20 | `test_set_and_get_conversation_state`                   | State + JSON stored and retrieved          | State-based             | ✅                       |
| 21 | `test_set_conversation_state_idempotent_update`         | Second write overwrites first cleanly      | Idempotency             | ✅                       |

---

## Findings

| ID | Severity  | Location                      | Description                                                                                                                                                                                           |
|----|-----------|-------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| F1 | 🔵 Low    | `test_webhook_routing.py:11`  | `VALID_ROLES` imported but never asserted. Dead import.                                                                                                                                               |
| F2 | 🔵 Low    | `test_webhook_routing.py:148` | Weak assertion — `"pending" in sent.last_text` is always true when the usage message is shown (VALID_ROLES list includes `"pending"`). The `or` makes the test pass regardless of which branch fires. |
| F3 | 🔵 Low    | `main.py:328`                 | `run_bootstrap_it` hardcodes name `"IT Admin"`. Self-corrects on first `/start` (upsert preserves role). Cosmetic.                                                                                    |
| F4 | 🔵 Low    | `tests/test_cli.py`           | No tests for `--register-webhook` or `--bootstrap-it` flags. Mutual exclusion guard and `RunMode.bootstrap_it` field not covered by CLI tests.                                                        |
| F5 | 🔵 Low    | `bot_hook.main()`             | CGI scaffolding (403 branch, `CONTENT_LENGTH` stdin read, `sys.stdout` header write) not unit-tested. Expected for S005 scope; note for future integration test coverage.                             |
| F6 | 🔴 Blocker | `bot_hook.py:11`             | `os.path.abspath(__file__)` does not follow symlinks. When executed via symlink from `public_html/`, `_ROOT` resolved to `~/public_html/` instead of `~/Shedule_bot/`, causing `ImportError` on `from db import …`. Result: empty HTTP response. **Found during Owner UAT. Fixed: changed to `os.path.realpath`.** |
| F7 | 🔴 Blocker | `bot_hook.py:14`             | CGI shebang uses base `/opt/alt/python311/bin/python3.11`, which cannot see venv packages. `import requests` failed silently, producing empty response. **Found during Owner UAT. Fixed: `_VENV` site-packages injected into `sys.path` at startup.** |
| F9 | 🟡 Minor   | `readme_WEBHOOK.md`, `readme_DEPLOY.md`, `.env.example`, UAT artifact | Placeholder `yourdomain.com` visually indistinguishable from a real domain — Owner followed the instruction literally without substituting. Breaches quality primitive: **Documentation / Placeholder clarity** — all placeholders must use `<ALL_CAPS>` format. **Fixed:** all occurrences replaced with `<YOUR_DOMAIN>`; placeholder legend table added to `readme_WEBHOOK.md`. |
| F8 | 🟡 Minor   | `readme_WEBHOOK.md` Step 1   | `chmod 755` instruction leaves server git working tree dirty on every subsequent `git pull` (`old mode 100644 / new mode 100755`). **Found during Owner UAT.** Breaches quality primitive: **Portability / Installability** — deployment must leave the server in a clean, repeatable state (ref: Development Plan quality table). Fix: add `git config --local core.fileMode false` as a one-time server step in `readme_WEBHOOK.md` Step 0. No source code change required. **Fixed.** |
| F10 | 🔴 Blocker | `readme_WEBHOOK.md` Step 1 / AD-S005-001 | AD-S005-001 specified CGI handler placement in `~/public_html/`. On Namecheap cPanel with LiteSpeed Web Server, Python CGI scripts placed in `public_html/` are not executed — LiteSpeed returns HTTP 404 for both GET and POST requests, and does not follow symlinks pointing outside the document root. Attempted fix (move to `cgi-bin/`) was also insufficient — see F11. **Superseded by F11.** |
| F11 | 🔴 Blocker | Hosting platform / AD-S005-001, AD-S005-009 | CGI execution is disabled server-wide on this Namecheap shared hosting account. Confirmed by testing a plain bash script (`test.sh`) in `~/public_html/cgi-bin/` — LiteSpeed returned HTTP 404. Adding `.htaccess` with `Options +ExecCGI` and `AddHandler cgi-script .py` had no effect. The entire S005 CGI delivery model is invalid for this hosting. Breaches quality primitive: **Portability / Installability** — deployment steps must produce a functioning system on the target hosting environment. **Root cause: Architect's hosting capability assumption (CGI available on cPanel/LiteSpeed) was not verified against the actual account.** Fix: replace CGI with WSGI/Passenger via cPanel "Setup Python App" — see AD-S005-010. **Fixed: `passenger_wsgi.py` deployed; POST returns `{}`.** |
| F12 | 🔴 Blocker | `.gitignore` | Passenger runtime creates `tmp/` (restart signal directory) and `stderr.log` in the app root (`~/Shedule_bot/`). Neither is in `.gitignore`, leaving `git status` dirty after deployment. A dirty working tree masks real changes — maintainer cannot reliably see what is modified on the server, and `git pull` output becomes misleading. **Found during Owner UAT.** Breaches quality primitive: **Portability / Installability** — deployment must leave the server in a clean, repeatable state; and **Maintainability / Analysability** — server state must be inspectable. Fix: add `tmp/` and `stderr.log` to `.gitignore`. **Fix applied (Developer, pending server `git pull`).** |
| F13 | 🟡 Minor   | `readme_WEBHOOK.md` Step 1 | Setup guide describes only creating a new Python App from scratch. Does not cover: existing app with wrong domain, virtualenv conflict (`Virtual environment already exists` error), or reconfiguration procedure. Owner encountered all three during UAT and had no documented guidance. Breaches quality primitive: **Documentation / Deployment traceability** — each step must cover expected obstacles and recovery paths. **Fix pending (Developer).** |

---

## Process finding — PF1

**Title:** Deployment procedure not verified as part of QA pass

**Finding:** F6, F7, F8, F10, and F11 were all discovered by the Owner during UAT execution, not by QA. All five are consequences of actually following the deployment steps on the real hosting environment — not code logic errors. QA reviewed the documentation for content correctness but did not execute the procedure or verify hosting capability assumptions against the actual server.

**Quality primitive breached:** Portability / Installability (Development Plan) — "deployment must leave the server in a clean, repeatable state."

**Root cause:** QA's definition of done for deployment documentation covered only *content review* (does the step make sense?), not *procedural verification* (does following the step produce the expected state?). Specifically, there was no checklist item asserting that after completing all steps, `git status` is clean and `curl` returns `{}`.

**Recommendation:** For any sprint that introduces or modifies deployment instructions, QA must add a *deployment checklist* review item: trace each step and assert the expected observable outcome (git state, curl response, command exit code). This does not require a live server — it can be done by inspection against known system behaviour.

### F2 — suggested fix

```python
# current (weak):
assert "pending" in sent.last_text or "Використання" in sent.last_text

# suggested:
assert "Використання" in sent.last_text
```

---

## Architecture decisions — verification

| AD          | Claim                               | Verified                                        |
|-------------|-------------------------------------|-------------------------------------------------|
| AD-S005-001 | CGI — no persistent process         | ❌ CGI delivery model invalid for this hosting — see F11. Replaced by WSGI/Passenger (AD-S005-010). `_handle()` pure function claim remains valid. |
| AD-S005-002 | `_handle` is a pure function        | ✅ Tested without any CGI env                    |
| AD-S005-003 | 200 written before processing       | ✅ `sys.stdout.write(...)` before `_handle` call |
| AD-S005-004 | 403 on wrong secret, before 200     | ✅ Early-exit branch before `sys.stdout.write`   |
| AD-S005-005 | `bot_hook.py` imports only `db.py`  | ✅ No import of `main.py`, `config.py`, etc.     |
| AD-S005-006 | `upsert_user` preserves role        | ✅ Covered by test #14                           |

---

## Overall verdict

**🔴 BLOCKED — F11 open.**  
Initial QA pass found no blockers (F1–F5 all 🔵 Low). Two blockers (F6, F7) were discovered during Owner UAT and fixed by Developer. A third blocker (F10) identified wrong CGI directory; attempted fix (`cgi-bin/`) also failed. A fourth blocker (F11) confirmed CGI is disabled server-wide — the entire CGI delivery model is invalid for this hosting. Architect approved replacement: WSGI/Passenger via cPanel "Setup Python App" (AD-S005-010). Developer implementing `passenger_wsgi.py`.

**Open blockers:** F11 resolved (`passenger_wsgi.py` deployed, POST returns `{}`). F12 open — `tmp/` and `stderr.log` not in `.gitignore`; server `git status` is dirty. Fix applied to `.gitignore` in repo; Owner must `git pull` on server to resolve.

**Open low items:** F1 (dead import), F3 (hardcoded name), F4 (missing CLI tests), F5 (CGI path not unit-tested). May be deferred to a future sprint.
