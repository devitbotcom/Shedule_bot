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

### KI-003 — Invalid year silently skips all validation
**Severity:** 🟡 Low
**Source:** backlog 006b2-01 / QA finding F2
**Planned:** S007+

In `bot_hook._cmd_draft`, if `year_str` cannot be parsed as integer, `year_int = None` and the entire `validate_draft_grid` call is skipped with no feedback to Head. Checks V1, V2, V3, V5, V7 do not require `year_int` and could still run.

---

### KI-004 — V6 inner `except` does not cover `TypeError`
**Severity:** 🟡 Low
**Source:** QA logic review 2026-05-08
**Planned:** S007+

`except (ValueError, OverflowError)` in the V6/V6b loop does not catch `TypeError`. If `year_int=None` reaches `date(None, month_int, day_int)`, `TypeError` escapes the inner catch, hits the outer `except Exception: pass`, and silently aborts all remaining V6/V6b checks for that call. Production is safe — `bot_hook` guards with `if year_int is not None` — but any direct caller (test or future integration) with `year_int=None` gets silent V6 suppression. Related to KI-003.

**Fix:** add `TypeError` to the inner `except` clause, or document `year_int` as required non-None in the function signature.

---

### KI-005 — V3 cascades when date column is missing
**Severity:** 🟡 Low
**Source:** QA logic review 2026-05-08
**Planned:** backlog / cosmetic

When `[Налаштування]` fires for a missing date column, `_cell(row, None)` returns `""` for every data row. V3 also fires: `[Структура] N рядків без номера дня`. Head receives two warnings for a single config problem. The `[Налаштування]` tag makes the root cause clear, but V3 is noise in this scenario.

**Fix:** skip V2/V3 collection loop when `day_col_idx is None`.

---

### KI-006 — Stale test assertion in `test_v4_leap_year_no_warning`
**Severity:** 🟡 Low
**Source:** QA finding F4 (2026-05-08)
**Planned:** next Developer pass

`test_v4_leap_year_no_warning` (line 78) asserts `not any("має бути" in w ...)`. The V4 message was updated to use `"очікується"` (AD-S006b2-008); `"має бути"` no longer appears anywhere. Test passes (valid grid produces no V4 warning), but the assertion no longer guards V4 false positives — it checks for text that does not exist.

**Fix:** change to `not any("[Структура]" in w and "очікується" in w for w in warnings)`.

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
