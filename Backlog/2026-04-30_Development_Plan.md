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

| Source                                    | Content                                        | Notes                                                                                                      |
|-------------------------------------------|------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| `schedule.xlsx`                           | Shift grid — one duty doctor per department per day | Columns identified by header name only, never by position. Required headers are constants in the parser. Missing header → exit 1. |
| `schedule.xlsx` col `Дата`               | Shift date                                     | —                                                                                                          |
| `schedule.xlsx` col `Day-type`            | `labor` / `holiday` / `other` per date         | Determines shift type and duty start time                                                                   |
| `schedule.xlsx` col `Ургенція спеціалістів на дому` | Ургенція block                     | Out of POC scope — column present in XLSX but not read; parser logs INFO and skips it                      |
| `contacts.json` (server only, not in Git) | Staff name → messenger channel + contact ID    | Hand-edited by IT Owner at deploy time                                                                     |

**contacts.json format:**
```json
[
  {
    "name": "Єрема В.Р.",
    "channels": { "telegram": "123456789" },
    "primary_channel": "telegram"
  }
]
```

**Shift type rule (derived from Day-type):**

| Day-type            | Duty shift tracked in XLSX   | Duty start |
|---------------------|------------------------------|------------|
| `labor`             | Night duty (17:00–09:00)     | 17:00      |
| `holiday` / `other` | 24h duty (09:00–09:00)       | 09:00      |

> Day staff (09:00–17:00, Mon–Fri) are regular employees not tracked in this schedule. The XLSX grid contains duty doctors only.

---

## Explicitly NOT in POC

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
| S002      | Foundation: config, CLI, DB, XLSX parser, shift logic + Docker local dev env | ⏳ Awaiting Owner UAT + Docker |
| S003      | Telegram adapter + orchestrator                                              | ⏸ Blocked on S002 UAT        |
| S004      | Production deploy: cPanel, cron, hardening                                   | ⏸                            |
| S005 `**` | Viber P2                                                                     | ⏸ Post-POC                   |
| S006 `*`  | Multi-ward v2                                                                | ⏸ Future                     |

## Quality Levels — POC

| Characteristic         | Sub-characteristic | POC scope                                                                               | Status      |
|------------------------|--------------------|-----------------------------------------------------------------------------------------|-------------|
| Functional suitability | Correctness        | All staff receive correct Telegram message. Verified by Owner UAT.                      | Not started |
| Reliability            | Fault tolerance    | Graceful error handling on all known failure modes. Exit 0/1. No silent skips.          | Not started |
| Reliability            | Recoverability     | Log written on every run including failures. SQLite audit trail per send attempt.       | Not started |
| Performance efficiency | —                  | Not measured — small staff volume, no SLA required.                                     | NA          |
| Usability              | Operability        | Health check, dry-run, production CLI modes produce human-readable output.              | Not started |
| Security               | Confidentiality    | No secrets in code or logs. `.env` and `contacts.json` not in Git. No PII in log output. | Not started |
| Compatibility          | Interoperability   | Standard XLSX (openpyxl), Telegram REST API, JSON contacts file.                        | Not started |
| Maintainability        | Modifiability      | IT updates `contacts.json` without touching code.                                       | Not started |
| Maintainability        | Testability        | Unit tests cover shift logic, parser, DB layer. No network calls in tests.              | Not started |
| Maintainability        | Analysability      | SQLite audit log. Log file on every run. CLI health check per component.                | Not started |
| Portability            | Installability     | One venv install + one cron line. New IT can deploy from README alone.                  | Not started |
| Portability            | Adaptability       | Local dev env (Docker) + production target (Namecheap cPanel, Python 3.11.14).          | Not started |

**S003 scope is locked.** All blocking items resolved. See Discussion doc for full Q&A record.
