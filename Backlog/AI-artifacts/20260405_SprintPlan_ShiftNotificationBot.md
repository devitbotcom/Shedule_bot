# Sprint Plan — Shift Schedule Notification Bot
**Project:** Shift Schedule Notification Bot  
**Date:** 2026-04-05  
**Status:** ✅ APPROVED

---

## SDLC Stages Per Sprint

Every sprint passes through all stages in order before closing.  
No stage begins until the previous one is signed off.

| # | Stage            | Stakeholder | Output Artifact                | Handoff condition                                   |
|---|------------------|-------------|--------------------------------|-----------------------------------------------------|
| 1 | **Architecture** | Architect   | `YYYYMMDD_Sprint00X_ARCH_*.md` | Architect approves scope and design                 |
| 2 | **Development**  | Developer   | `YYYYMMDD_Sprint00X_DEV_*.md`  | Implementation plan complete, code directives clear |
| 3 | **QA**           | QA Engineer | `YYYYMMDD_Sprint00X_QA_*.md`   | Test plan and test cases written                    |
| 4 | **UAT**          | Owner       | Checklist in QA artifact       | Owner signs off — sprint closes                     |

> **AI execution model:** Architect → Developer → QA roles are played by AI in sequence within one session.  
> Execution pauses and hands off to Owner for: UAT sign-off, business decisions, or any question marked *(assigned to: Owner)*.

---

## Stakeholder Roles

| Role            | Responsibility                                                   |
|-----------------|------------------------------------------------------------------|
| **Owner**       | Business decisions, UAT sign-off, XLSX management, cPanel access |
| **Architect**   | Technical design, module contracts, risk, acceptance criteria    |
| **Developer**   | Implementation directives, code structure, integration rules     |
| **QA Engineer** | Test plan, test cases, test data, pass/fail criteria             |
| **Consultant**  | External review, risk flags (feeds into Architect decisions)     |

---

## Sprint Register

| Sprint | Scope                                                           | P  | Stage | Status                                                 |
|--------|-----------------------------------------------------------------|----|-------|--------------------------------------------------------|
| S001   | Architecture — full system design                               | P1 | UAT   | ✅ CLOSED — Owner approved                              |
| S002   | Foundation: scaffold, config, CLI, DB, XLSX parser, shift logic | P1 | DEV   | ⏳ ARCH✅ DEV revised (CR-001) — awaiting Docker test run + Owner UAT |
| S003   | Telegram adapter + full orchestrator (main.py)                  | P1 | —     | ⏸ blocked by S002 UAT                                  |
| S004   | Production deploy: Namecheap, cron, hardening                   | P1 | —     | ⏸ blocked by S003                                      |
| S005   | Viber P2: API verification, adapter, staff onboarding           | P2 | —     | ⏸ blocked by S004 + Viber API gate                     |
| S006   | Multi-ward v2: location column, multi-instance deploy           | v2 | —     | ⏸ future                                               |

---

## Sprint Gates (UAT Criteria Summary)

### S002 — Foundation
Owner can:
- Run `python main.py` → health check returns ✅ for config, DB, XLSX
- Run `python main.py --dry-run` → correct shift data printed for all employees, zero messages sent
- Run with broken config → clear error, exit code 1

### S003 — Telegram + Orchestrator
Owner can:
- Run `python main.py --production` → all shifts receive correctly formatted Telegram messages in the group chat (CR-001: group mode for POC)
- Verify `notifications` table populated in DB
- Verify log written to `~/logs/`
- Run `python main.py --production --employee "Name"` → one shift message sent to group

### S004 — Production Deploy
Owner can:
- Trigger cron manually from cPanel → messages received by real staff
- Run `python main.py` on server → full health check ✅
- Verify log files written on server
- Verify `shift_bot.db` and `~/logs/` are not publicly accessible
- Run `--reload-schedule` after XLSX update → dedup cleared, cron re-sends on next fire

### S005 — Viber P2
Owner can:
- Run `python main.py --production` → Viber staff receive messages alongside Telegram staff
- Full health check includes Viber bot status ✅

---

## Artifact Naming Convention

```
AI-artifacts/
  YYYYMMDD_Sprint00X_ARCH_ShiftNotificationBot.md   ← Architecture
  YYYYMMDD_Sprint00X_DEV_ShiftNotificationBot.md    ← Developer directives
  YYYYMMDD_Sprint00X_QA_ShiftNotificationBot.md     ← Test plan
```

Sprint 001 ARCH artifact already exists:  
→ [`20260405_Sprint001_ARCH_ShiftNotificationBot.md`](20260405_Sprint001_ARCH_ShiftNotificationBot.md)

---

## Handoff Protocol

1. AI completes Architect stage → presents to Owner for scope confirmation if needed → proceeds to Developer
2. AI completes Developer stage → proceeds to QA
3. AI completes QA stage → presents UAT checklist to Owner
4. **Owner executes UAT** — tests against the checklist on real environment
5. Owner records result (pass / fail / partial) in the QA artifact
6. Sprint closes → next sprint begins

> If Owner finds a defect during UAT: QA raises a bug, Developer fixes, QA re-tests, Owner re-validates.  
> The sprint does not close until all UAT items pass.
