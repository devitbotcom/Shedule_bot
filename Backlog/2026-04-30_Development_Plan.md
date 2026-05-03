# Development Plan — Shift Schedule Notification Bot
**Date:** 2026-04-30  
**Requirements:** 
- [`2026-04-05_01-PRL`](2026-04-05_01-PRL.md)  

**Diagrams:** 
- [Duty Shift Schema](shifts.puml) 
- [Business Flow](shifts_notification_businessflow.puml)

> `*` in roadmap = not planned for MVP &nbsp;&nbsp; `**` = not planned for POC

---

## POC Scope

Each staff member (per department) listed in the XLSX schedule grid receives one personal Telegram message per shift. 

Message format:

```
Зміна: {department_title} {date}
{staff_name} заступає на зміну замість {previous_staff_name}.

Наступна зміна:
{next_date} о {next_time} — {next_staff_name}
```

`{date}` / `{next_date}` format: `DD-MM-YYYY` (e.g. `07-04-2026`). `{next_time}`: `17:00` for `labor` day, `09:00` for `holiday` / `other`. Missing prev/next: `"-"` substituted, line not omitted.

Triggered by a cPanel cron job. Runs on Namecheap shared hosting. No daemons, no webhooks.

---

## What the POC reads

| Source                                              | Content                                             | Notes                                                                                                                             |
|-----------------------------------------------------|-----------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| `schedule.xlsx`                                     | Shift grid — one duty doctor per department per day | Columns identified by header name only, never by position. Required headers are constants in the parser. Missing header → exit 1. |
| `schedule.xlsx` col `Дата`                          | Shift date                                          | —                                                                                                                                 |
| `schedule.xlsx` col `Day-type`                      | `labor` / `holiday` / `other` per date              | Determines shift type and duty start time                                                                                         |
| `schedule.xlsx` col `Ургенція спеціалістів на дому` | Ургенція block                                      | Out of POC scope — column present in XLSX but not read; parser logs INFO and skips it                                             |
| `.env` var `TELEGRAM_GROUP_CHAT_ID`                 | Telegram group chat ID                              | All shift notifications sent to this group. IT creates group, adds bot, copies ID.                                               |

**Shift type rule (derived from Day-type):**

| Day-type            | Duty shift tracked in XLSX   | Duty start |
|---------------------|------------------------------|------------|
| `labor`             | Night duty (17:00–09:00)     | 17:00      |
| `holiday` / `other` | 24h duty (09:00–09:00)       | 09:00      |

> Day staff (09:00–17:00, Mon–Fri) are regular employees not tracked in this schedule. The XLSX grid contains duty doctors only.

---

## Explicitly NOT in POC

- Group @mentions (POC2, S005) — needs Telegram username per doctor; plain group text for now
- Personal Telegram DMs (S006) — individual chat_id per doctor; deferred post-POC
- Ургенція specialists (column K) — not parsed, not notified; deferred to post-POC
- Viber messenger — deferred to P2 after POC is live and stable
- Multi-ward / multi-location
- Confirmation button / two-way conversation (requires persistent process — post-POC)
- Real-time shift swaps, payroll integration, web UI

---

## Definition of Done — POC

Owner runs `python main.py --production` on the server and:
- All staff in the XLSX receive a correctly formatted Telegram message
- `notifications` table in SQLite is populated with one record per send
- Log file written to `~/logs/`
- `python main.py` (health check) returns all ✅
- No credentials or PII appear in any log output

---

## Roadmap

| Phase    | Scope                                                                                 | Status                                                                        |
|----------|---------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| S001     | Architecture                                                                          | ✅ Done                                                                        |
| S002     | Foundation: config, CLI, DB, XLSX parser, shift logic + Docker local dev env          | ✅ Done — Owner UAT accepted 2026-04-30                                        |
| S003     | Telegram adapter + orchestrator — group chat, plain text (POC)                        | ✅ Done — Owner UAT accepted 2026-04-30                                        |
| S004     | Local automation: Docker cron service (supercronic), dynamic crontab from shift_hours | ✅ Done — NFR-S004-001 resolved; UAT accepted                                  |
| S004b    | Production deploy: Namecheap cPanel, venv, hardening                                  | ⏳ Owner UAT in progress — crontab auto-install confirmed on server 2026-05-03 |
| S011 `*` | POC2 - USER registers himself to group chat (Permisison for IT, Head, Doctor)         | ⏸ POC2                                                                        |
| S012 `*` | POC2 - Head requests to generate schedule (dialogue to provide time preferences)      | ⏸ POC2                                                                        |
| S012 `*` | POC2 - Head asks for his department schedule                                          | ⏸ POC2                                                                        |
| S?? `*`  | POC2 — group chat + @mention per doctor (needs username contact list)                 | ⏸ Post-POC                                                                    |
| S?? `**` | Personal DMs — individual chat_id per doctor                                          | ⏸ Post-POC                                                                    |
| S?? `**` | Viber messenger adapter                                                               | ⏸ Post-POC                                                                    |
| S?? `*`  | Multi-ward v2                                                                         | ⏸ Future                                                                      |

---

## Quality Characteristics — POC-1

*Updated 2026-05-01 with primitives discovered during S003–S004.*

| Characteristic         | Sub-characteristic       | Requirement                                                                                        | Discovered / Raised       | Status         |
|------------------------|--------------------------|----------------------------------------------------------------------------------------------------|---------------------------|----------------|
| Functional suitability | Correctness              | All staff receive correct Telegram message. Verified by Owner UAT.                                 | S001                      | ✅ S003         |
| Functional suitability | Completeness             | prev/next colleague resolved across date boundaries — full month context required.                  | BUG-005 (S003)            | ✅ S003         |
| Reliability            | Fault tolerance          | Graceful error on all known failure modes. Exit 0/1. No silent skips.                              | S001                      | ✅ S003         |
| Reliability            | Recoverability           | Log written on every run including failures. SQLite audit trail per send attempt.                  | S001                      | ✅ S003         |
| Reliability            | Schedule correctness     | Cron fires at the time the Maintainer expects — `TZ` must match Maintainer's local timezone.       | NFR-S004-001 (S004 UAT)   | ✅ S004b — `TZ=` prefix in every cron entry; `time.tzset()` fix in `config.py`; `--gen-crontab` calculates server-local times automatically |
| Performance efficiency | —                        | Not measured — small staff volume, no SLA required.                                                | —                         | NA             |
| Usability              | Operability              | Health check, dry-run, production CLI modes produce human-readable output.                         | S001                      | ✅ S003         |
| Usability              | Configurability          | IT edits only `data/schedule_mapping.json` for shift timing — no crontab syntax knowledge needed.  | 004-2 (S004 UAT)          | ✅ S004         |
| Security               | Confidentiality          | No secrets in code or logs. `.env` not in Git. No PII in log output. Token never in exceptions.   | S001 + BUG-S004-001       | ✅ S004         |
| Compatibility          | Interoperability         | Standard XLSX (openpyxl), Telegram REST API. Adapter pattern isolates messenger dependency.        | S001                      | ✅ S003         |
| Maintainability        | Modifiability            | IT updates `.env` (group chat ID, timezone) without touching code.                                 | S001 + S004               | ✅ S004b — `--gen-crontab` reinstalls cron on any `shift_hours` change; readme_DEPLOY.md P9b covers procedure |
| Maintainability        | Testability              | Unit tests cover all logic layers. No network calls in tests. Subprocess tests for scripts.        | S001 + QA S004            | ✅ S004         |
| Maintainability        | Analysability            | SQLite audit log. Timestamped log file on every run. CLI health check per component.              | S001                      | ✅ S003         |
| Maintainability        | Single source of truth   | `shift_hours` in `schedule_mapping.json` drives both message content and cron schedule.            | 004-2 (S004 UAT)          | ✅ S004         |
| Portability            | Installability           | `docker compose up -d cron` is the only command IT needs for local dev. Production: `--gen-crontab` installs all cron entries automatically — no cPanel UI interaction. | S004 + S004b              | ✅ S004b        |
| Portability            | Adaptability             | Messenger adapter pattern supports adding Viber (S007) without changes to orchestrator or parser.  | S001 + S004 ext           | ⏸ S007         |

---

## Messenger Extensibility Architecture

*Registered 2026-05-01 — formalises the adapter pattern for future messenger integrations.*

### Current state

| Messenger | Adapter                         | Sprint  | Status    |
|-----------|---------------------------------|---------|-----------|
| Telegram  | `messenger/telegram_adapter.py` | S003    | ✅ Live    |
| Viber     | `messenger/viber_adapter.py`    | S007    | ⏸ Planned |

### Extension contract

All messenger adapters implement `MessengerGateway` (`messenger/gateway.py`):

```python
class MessengerGateway:
    def send(self, contact_id: str, message: str) -> None: ...
    def health_check(self) -> bool: ...
```

**Adding a new messenger (e.g. Viber, S007):**

1. Create `messenger/viber_adapter.py` implementing `MessengerGateway`
2. Add `VIBER_BOT_TOKEN` (or equivalent) to `.env.example` and `config.py`
3. `Shift.messenger` field routes to the correct adapter at runtime — no changes to parser, shift logic, or DB layer
4. Token sanitization rule (AD-S004-007) applies to all adapters — never propagate raw network exceptions

**Isolation requirement:** Each adapter catches its own network exceptions and re-raises a sanitized `RuntimeError`. The orchestrator (`run_production()`) must never receive a token-bearing exception string from any adapter.

### Planned: S??? Viber adapter

| Item                          | Notes                                                                        |
|-------------------------------|------------------------------------------------------------------------------|
| `VIBER_BOT_TOKEN` env var     | Added to `.env.example`                                                      |
| `messenger/viber_adapter.py`  | Implements `send()` and `health_check()`                                     |
| `contacts.json` re-introduced | Per-person routing: `{"name": ..., "messenger": "viber", "contact_id": ...}` |
| Dedup key unchanged           | employee + date — messenger-agnostic                                         |

---

## Owner Observations Backlog

Issues raised by Owner during UAT that have been resolved or deferred.

| ID           | Sprint  | Description                                                   | Resolution                                                                                                                                                          |
|--------------|---------|---------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 004-1        | S004    | Logs for review — IT needs to find when feature was used      | ✅ Two log locations: `data/logs/` file + `docker compose logs cron`. README to document both.                                                                       |
| 004-2        | S004    | Two scheduling configs: `crontab` + `schedule.xlsx`           | ✅ Resolved: `shift_hours` in `schedule_mapping.json` now drives cron schedule via `gen_crontab.py`. Single source of truth.                                         |
| NFR-S004-001 | S004b   | Cron time interpreted in UTC, not Maintainer's local timezone | ✅ Resolved S004b: `TZ=Europe/Kyiv` prefix on every cron entry; `time.tzset()` in `config.py`; `--gen-crontab` computes server-local times from offset automatically |

**S003 scope is locked.** All blocking items resolved. See Discussion doc for full Q&A record.

---

## Change Request — CR-001 ✅ RESOLVED

**Date raised:** 2026-04-30  
**Resolved:** 2026-04-30  
**Decision: Option B — Group chat for POC. Personal DMs deferred to post-POC.**

**Rationale:** Collecting individual Telegram chat_ids from every staff member is unnecessary onboarding complexity for a POC. A shared group removes that barrier entirely.

**Architectural decisions:**

| Area                    | Decision                                                                       |
|-------------------------|--------------------------------------------------------------------------------|
| Notification target     | One `TELEGRAM_GROUP_CHAT_ID` (env var) — all shifts notified to this group     |
| `contacts.json`         | **Dropped for POC** — no external name registry required                       |
| `CONTACTS_PATH` env var | **Replaced** by `TELEGRAM_GROUP_CHAT_ID`                                       |
| Name validation         | Parser accepts any non-empty string from XLSX (no cross-check)                 |
| `Shift.contact_id`      | Populated from config group chat_id — same value for all shifts                |
| `Shift.messenger`       | Always `"telegram"` for POC                                                    |
| `Shift` model           | **Unchanged** — post-POC upgrade restores per-person routing via contacts.json |
| Message content         | Unchanged — one message per shift, same template, sent to group                |

**Post-POC path:** Reintroduce `contacts.json` with individual chat_ids + `CONTACTS_PATH` env var. No model or adapter changes required.

**S002 code changes required (Developer):**

| File                            | Change                                                                         |
|---------------------------------|--------------------------------------------------------------------------------|
| `config.py`                     | Replace `CONTACTS_PATH` with `TELEGRAM_GROUP_CHAT_ID`                          |
| `.env.example`                  | Update accordingly                                                             |
| `schedule_parser.py`            | Remove `_load_contacts`; signature: `parse_schedule(xlsx_path, group_chat_id)` |
| `main.py`                       | Pass `config["TELEGRAM_GROUP_CHAT_ID"]` to `parse_schedule`                    |
| `data/contacts.json.example`    | Repurpose as post-POC reference only — add a note                              |
| `tests/test_config.py`          | `CONTACTS_PATH` → `TELEGRAM_GROUP_CHAT_ID`                                     |
| `tests/test_schedule_parser.py` | Remove contacts fixture dependency; pass group_chat_id directly                |
| `README.md`                     | Update IT setup section — group ID setup already added by Owner                |
