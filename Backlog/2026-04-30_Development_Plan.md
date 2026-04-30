# Development Plan — Shift Schedule Notification Bot
**Date:** 2026-04-30  
**Requirements:** [`2026-04-05_01-PRL`](2026-04-05_01-PRL.md)

---

## Goal
Send each staff member a personal message with their duty, shift time, and prev/next shift colleague. Triggered by cron. Hosted on Namecheap cPanel.

Business case:
Staff is always informed his current schedule and who is his shift. 

See [Duty Shift Schema](./shifts.puml)

See [Shift Notification Flow](./shifts_notification_businessflow.puml)

---

## Phases

| #    | Scope                                                  | Status                |
|------|--------------------------------------------------------|-----------------------|
| S001 | Architecture                                           | ✅ Done                |
| S002 | Foundation: config, CLI, DB, XLSX parser, shift logic  | ⏳ Awaiting Owner UAT  |
| S003 | Telegram adapter + orchestrator                        | ⏸ Blocked — see below |
| S004 | Production deploy (cPanel, cron, hardening)            | ⏸                     |
| S005 | Viber P2                                               | ⏸ Deferred post-POC   |
| S006 | Multi-ward v2                                          | ⏸ Future              |

---

## Blocked — decisions needed before S003

**A — XLSX holiday column**  
Shift type (Day/Night/24h) depends on whether a date is a workday or holiday.  
Proposal: add a `Тип дня` column — `Р` (workday) or `В` (holiday/weekend).  

OWNER: 
I have added new column A "Day-type" (shifted other columns right) it only labor, holiday or other. Hope we will newer need the other, but let make it just in case.

**B — Contacts file**  
Employee registry (name → messenger + chat ID) lives as a server-side file, not in Git.  
Proposal: `contacts.json`, hand-edited by IT Owner at deploy time.  
OWNER: 


For MVP is maybe only  
```JSON
[
    {
        "name": "Mihai Ionescu",
        "channels": {
        "telegram": "222456789"
        },
        "primary_channel": "telegram"
  }
]
```
---

## Out of scope for POC
- Ургенція staff notifications (column K) — deferred to post-POC
- Viber adapter (P2)
- Multi-ward / multi-location
- Real-time shift swaps, payroll, web UI
