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
| AD-S005-001 | CGI — no persistent process         | ✅ `bot_hook.py` exits after `main()`            |
| AD-S005-002 | `_handle` is a pure function        | ✅ Tested without any CGI env                    |
| AD-S005-003 | 200 written before processing       | ✅ `sys.stdout.write(...)` before `_handle` call |
| AD-S005-004 | 403 on wrong secret, before 200     | ✅ Early-exit branch before `sys.stdout.write`   |
| AD-S005-005 | `bot_hook.py` imports only `db.py`  | ✅ No import of `main.py`, `config.py`, etc.     |
| AD-S005-006 | `upsert_user` preserves role        | ✅ Covered by test #14                           |

---

## Overall verdict

**✅ PASS — no blockers.**  
F2 is the only finding worth addressing before Owner UAT (tightening one assertion). F1–F5 are all 🔵 Low. Critical security path (role gating for `/setrole`) correctly implemented and tested.

**Recommended action before UAT:** fix F2 (one-line change). F1–F5 may be deferred.
