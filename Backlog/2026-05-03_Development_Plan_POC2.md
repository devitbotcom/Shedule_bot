# Development Plan — POC2: Schedule Generation & Head Dialogue

**Date:** 2026-05-03
**PRL:** [`2026-05-03_02-PRL.md`](2026-05-03_02-PRL.md) extends [`2026-04-05_01-PRL.md`](2026-04-05_01-PRL.md)
**Depends on:** POC1 complete (S001–S004b)

---

## Goal

Head triggers the bot via Telegram, receives an algorithmically generated full-month duty schedule, refines it with free-text constraints (AI-normalised), and gets the result as XLSX ready for the existing POC1 send pipeline.

---

## Scope

| In | Out |
|---|---|
| Telegram inbound: **webhook** (Telegram POSTs to cPanel HTTPS endpoint) | Polling / cron-based message reading |
| Role registry: IT / Head / Staff | Viber |
| Algorithmic full-month schedule generation | AI-generated schedule |
| Head dialogue: generate → review → refine | Payroll, web UI |
| AI normalisation of free-text constraints (Input 6) | Multi-location |
| XLSX export matching POC1 input format | Staff self-registration (post-POC2) |
| XLSX / Google Drive URL validation for gaps (SHOULD) | Google Drive write-back |
| POC1 notification pipeline: **unchanged, zero regression** | — |

---

## Roadmap

| Sprint | Scope | Status |
|---|---|---|
| S005 | Bot listener: `getUpdates` polling, command routing, role registry, conversation state in DB | ⏸ Planned |
| S006 | Schedule generation algorithm: full month, shift rules, balanced allocation, XLSX export | ⏸ Planned |
| S007 | Head dialogue: `/generate` command, draft review, free-text → AI normalisation → refinement loop | ⏸ Planned |
| S008 | XLSX / Google Drive URL validation: gap check, rule violations, report to Head (SHOULD) | ⏸ Planned |

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

| # | Question | Needed for |
|---|---|---|
| OQ-1 | How many staff per department? (affects algorithm balance) | S006 |
| OQ-2 | Can one staff member appear in multiple departments? | S006 |
| OQ-3 | Does Head approve the final schedule inside the bot, or export and approve externally? | S007 |
| OQ-4 | Google Drive URL — public share link or Drive API with auth? | S008 |
