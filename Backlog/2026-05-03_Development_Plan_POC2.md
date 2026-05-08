# Development Plan — POC2: Schedule Generation & Head Dialogue

**Date:** 2026-05-03
**PRL:** [`2026-05-03_02-PRL.md`](2026-05-03_02-PRL.md) extends [`2026-04-05_01-PRL.md`](2026-04-05_01-PRL.md)
**Depends on:** POC1 complete (S001–S004b)

---

## Goal

Head triggers the bot via Telegram, receives an algorithmically generated full-month duty schedule, and refines it with free-text constraints (AI-normalised). The result is exported in a format compatible with the POC1 notification pipeline. Scheduling and notifications are independent processes — IT runs notifications separately.

---

## Scope

| In                                                                      | Out                                  |
|-------------------------------------------------------------------------|--------------------------------------|
| Telegram inbound: **webhook** (Telegram POSTs to cPanel HTTPS endpoint) | Polling / cron-based message reading |
| Role registry: IT / Head / Staff                                        | Viber                                |
| Algorithmic full-month schedule generation                              | AI-generated schedule                |
| Head dialogue: generate → review → refine                               | Payroll, web UI                      |
| AI normalisation of free-text constraints (Input 6)                     | Multi-location                       |
| XLSX export matching POC1 input format                                  | Staff self-registration (post-POC2)  |
| XLSX / Google Drive URL validation for gaps (SHOULD)                    | Google Drive write-back              |
| POC1 notification pipeline: **unchanged, zero regression**              | —                                    |

---

## Roadmap

| Sprint  | Scope                                                                                                                                                                      | Status                                                                     |
|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| S005    | Webhook infrastructure: Passenger/WSGI on cPanel, user registration, role system, commands `/start` `/whoami` `/help` `/setrole`                                           | ✅ Accepted 2026-05-05 — backlog 005-1, 005-2 on-hold; F12/F13 non-blocking |
| S006a   | Google Sheets integration — read staff list and schedule grid from named Google Sheet tab; scheduling input/output stays in Sheets; no connection to notification pipeline | ✅ Accepted 2026-05-06                                                      |
| S006b   | Schedule generation — weighted greedy algorithm; input: staff list + month/year from Google Sheet; output: `Draft-by-bot` tab in Google Sheet; `/draft` command for Head   | ✅ Accepted 2026-05-07                                                      |
| S006b2  | Draft validation warnings — non-blocking checks (empty staff, day count, day order, Sat/Sun vs holiday); appended to `/draft` reply and logged                             | 🏗 ARCH complete 2026-05-07                                                |
| S006c   | Head preferences — pre-filled cells in Draft tab treated as fixed constraints; algorithm skips non-empty cells during generation                                           | ⏸ Planned                                                                  |
| S006d   | ~~Dropped~~ — XLSX export is manual: IT downloads approved file from Google Sheets, copies to server as `schedule.xlsx`                                                    | ❌ Dropped 2026-05-07                                                       |
| S007    | Head dialogue: free-text → AI normalisation → constraint application → regeneration loop                                                                                   | ⏸ Planned                                                                  |
| S008    | XLSX / Google Drive URL validation: gap check, rule violations, report to Head (SHOULD)                                                                                    | ⏸ Planned                                                                  |

---

## Key Architectural Decisions

**Webhook** — Telegram POSTs each message to a cPanel HTTPS endpoint immediately. Near-zero latency. No persistent process. Same "run and exit" model as POC1. Cron polling dropped.

**Conversation state** — new `conversations` table in existing `shift_bot.db`: `(user_id, role, state, context_json, updated_at)`. State machine per user (idle → generating → reviewing → refining).

**Role system** — three roles: `it`, `head`, `staff`. IT assigns roles via bot command or direct DB edit. Role gates which commands are available.

**Schedule algorithm** — round-robin per department across staff pool, one slot per day. Respects `shift_hours` and `labor`/`holiday`/`other` day types from existing `schedule_mapping.json`. Output XLSX matches POC1 parser input format exactly — POC1 send pipeline reused unchanged.

**AI normalisation (Input 6)** — Head sends free-text (e.g. "Іваненко не може 5–10 травня"). Claude API call converts it to structured constraint `{staff, dates, rule}`. Bot applies constraint and regenerates. Non-blocking: if API unreachable, bot asks Head to rephrase as a command.

**XLSX validation (S008)** — reuses existing `parse_schedule` logic. Head uploads file or provides Google Drive share URL; bot downloads, runs parser, reports gaps and rule violations as a numbered list.

---

## Open Questions

| #    | Question                                                                               | Needed for | Answer                                          |
|------|----------------------------------------------------------------------------------------|------------|-------------------------------------------------|
| OQ-1 | How many staff per department? (affects algorithm balance)                             | S006       | We have stff list in xlsx (several dozens)      |
| OQ-2 | Can one staff member appear in multiple departments?                                   | S006       | Usually not, but it is possible as exception    |
| OQ-3 | Does Head approve the final schedule inside the bot, or export and approve externally? | S007       | Head uploads (apporcval happens outside of bot) |
| OQ-4 | Google Drive URL — public share link or Drive API with auth?                           | S008       | For test can start wit public. Auth for prod.   |
