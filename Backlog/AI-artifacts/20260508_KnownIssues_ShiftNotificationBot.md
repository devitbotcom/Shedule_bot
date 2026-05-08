# Known Issues — Shift Notification Bot
**Date:** 2026-05-08
**Prepared by:** QA
**Scope:** All open issues as of S006b2 + post-sprint logic review

---

## Legend

| Severity | Meaning |
|---|---|
| 🔴 P1 | Blocks production use or causes silent data loss |
| 🟠 P2 | Visible gap for IT/support; workaround exists |
| 🟡 Low | Test quality, edge case, or minor UX noise |
| 🔵 Risk | Not yet confirmed broken; deferred UAT or untested path |

---

## Open issues

### KI-001 — `--health` does not check Google Sheets connectivity
**Severity:** 🔴 P1
**Source:** backlog 006b-01
**Planned:** S006c+

`--health` passes even when Google Sheets credentials are invalid or the sheet is unreachable. A misconfigured service account or wrong `GOOGLE_SHEET_ID` goes undetected until `/draft` fails at runtime.

---

### KI-002 — Webhook handler does not log incoming requests
**Severity:** 🟠 P2
**Source:** backlog 006b-02
**Planned:** S006c+

Only errors are written to `webhook.log`. Each incoming Telegram update is not recorded, making silent failures (bot receives message, does nothing) invisible to IT without manual debugging.

---

### KI-011 — V8: same day in both preferred and undesired lists (per person)
**Severity:** 🟠 P2
**Source:** UAT finding 06c-03 / Owner decision 2026-05-08
**Planned:** S006d

If a staff member has the same day number in both `preferred_days` and `undesired_days`, the entry is contradictory. Current behaviour: preferred tier silently wins. Expected behaviour: exclude that person from assignment on that day; warn Head.

**Design:** see S006c ARCH §Deferred to S006d — V8.

---

### KI-012 — V9: day number out of valid range in preference lists
**Severity:** 🟠 P2
**Source:** UAT finding 06c-03 / Owner decision 2026-05-08
**Planned:** S006d

Day numbers outside the valid range `1…month_length` (including 0, negatives, and over-length values such as 32) in `preferred_days` or `undesired_days` indicate a data-entry error. Zero and negatives pass through `_parse_days` as valid integers. No warning is currently issued for any of these cases.

**Design:** see S006c ARCH §Deferred to S006d — V9.

---

### KI-013 — V10: all staff in a department share the same preferred day
**Severity:** 🟡 Low
**Source:** UAT finding 06c-03 / Owner decision 2026-05-08
**Planned:** S006d

When every candidate for a department has the same day in their `preferred_days`, the preference cannot discriminate and the slot outcome is the same as without preferences. Current behaviour: preference logic still runs (one candidate wins the preferred tier). Expected behaviour: skip preference logic for that day in that department, treat all as neutral, warn Head.

**Design:** see S006c ARCH §Deferred to S006d — V10.

---

### KI-007 — Admin role requires bot interaction, not config file
**Severity:** 🟡 Low (on hold)
**Source:** backlog 005-1

IT admin role can only be bootstrapped via `--bootstrap-it` CLI. No way to pre-seed roles from a config file without running the bot.

---

### KI-008 — Bot responds to any message, not only commands
**Severity:** 🟡 Low (on hold)
**Source:** backlog 005-2

Bot replies "Невідома команда" to chat messages, user join events, and any non-command text. Noisy in group chats.

---

### KI-010 — `/draft` success reply has no link to the Google Sheet
**Severity:** 🟡 Low
**Source:** UAT feedback 06b-03
**Planned:** backlog

The positive `/draft` reply does not include a link to the output sheet. Head must navigate manually after running the command. `GOOGLE_SHEET_ID` is already available in `bot_hook._cmd_draft` — the link can be appended to the success message.

Expected addition to reply:
```
🔗 https://docs.google.com/spreadsheets/d/<SHEET_ID>
```

---

### KI-009 — `/help` for IT admin role not verified in UAT
**Severity:** 🔵 Risk (deferred)
**Source:** backlog 005-3

U005-5 (verify `/setrole` appears in `/help` for IT role) was skipped during S005 UAT. Not confirmed broken but untested in production.

---

## Resolved (closed)

| ID | Description | Fixed |
|---|---|---|
| F1 | `import pytest` unused in `test_schedule_validator.py` | 2026-05-08 |
| F3 | V5 `for…else` dead code | 2026-05-08 |
| 06b2-3 | V2 not firing on `None` cell (gspread empty) | 2026-05-08 |
| 06b2-1 | Mon–Fri not checked for `holiday` day-type | 2026-05-08 |
| 06b2-2 | V5 message unreadable; warnings not written to tab | 2026-05-08 |
| 06b-04 | Period in initials rejected by V7 name regex | 2026-05-08 |
| KI-003 | Invalid year silently skips all validation | S006c C3 |
| KI-004 | V6 inner `except` does not cover `TypeError` | S006c C3 (`year_int: int \| None`; V6 guarded internally) |
| KI-005 | V3 cascades when date column is missing | S006c C4 |
| KI-006 | Stale T5a test assertion (`"має бути"`) | S006c C5 |
| KI-010 | `/draft` reply has no link to Google Sheet | S006c C2 |
