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

Each staff member listed in the XLSX schedule grid receives one personal Telegram message per shift. Message format:

```
Зміна: {date}
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

| Phase     | Scope                                                                        | Status                       |
|-----------|------------------------------------------------------------------------------|------------------------------|
| S001      | Architecture                                                                 | ✅ Done                       |
| S002      | Foundation: config, CLI, DB, XLSX parser, shift logic + Docker local dev env | ✅ Done — Owner UAT accepted 2026-04-30 |
| S003      | Telegram adapter + orchestrator — group chat, plain text (POC)               | ⏳ DEV complete — awaiting QA + Owner UAT |
| S004      | Production deploy: cPanel, cron, hardening                                   | ⏸                            |
| S005 `*`  | POC2 — group chat + @mention per doctor (needs username contact list)        | ⏸ Post-POC                   |
| S006 `**` | Personal DMs — individual chat_id per doctor                                 | ⏸ Post-POC                   |
| S007 `**` | Viber P2                                                                     | ⏸ Post-POC                   |
| S008 `*`  | Multi-ward v2                                                                | ⏸ Future                     |

## Quality Levels — POC

| Characteristic         | Sub-characteristic | POC scope                                                                               | Status      |
|------------------------|--------------------|-----------------------------------------------------------------------------------------|-------------|
| Functional suitability | Correctness        | All staff receive correct Telegram message. Verified by Owner UAT.                      | Not started |
| Reliability            | Fault tolerance    | Graceful error handling on all known failure modes. Exit 0/1. No silent skips.          | Not started |
| Reliability            | Recoverability     | Log written on every run including failures. SQLite audit trail per send attempt.       | Not started |
| Performance efficiency | —                  | Not measured — small staff volume, no SLA required.                                     | NA          |
| Usability              | Operability        | Health check, dry-run, production CLI modes produce human-readable output.              | Not started |
| Security               | Confidentiality    | No secrets in code or logs. `.env` not in Git. No PII in log output.                     | Not started |
| Compatibility          | Interoperability   | Standard XLSX (openpyxl), Telegram REST API.                                            | Not started |
| Maintainability        | Modifiability      | IT updates `.env` (group chat ID) without touching code.                                | Not started |
| Maintainability        | Testability        | Unit tests cover shift logic, parser, DB layer. No network calls in tests.              | Not started |
| Maintainability        | Analysability      | SQLite audit log. Log file on every run. CLI health check per component.                | Not started |
| Portability            | Installability     | One venv install + one cron line. New IT can deploy from README alone.                  | Not started |
| Portability            | Adaptability       | Local dev env (Docker) + production target (Namecheap cPanel, Python 3.11.14).          | Not started |

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
