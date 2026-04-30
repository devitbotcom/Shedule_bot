# QA Review — Development Plan
**Date:** 2026-04-30  
**Role:** QA Analyst  
**Subject:** `2026-04-30_Development_Plan.md` + `2026-04-05_01-PRL`  
**Status:** ✅ All Owner answers recorded. Architect decisions applied. Q16 (XLSX header names) still pending Owner confirmation.

---

## Summary

The Development Plan is well-structured and covers scope, decisions, and quality levels clearly. The issues below are **not defects in the plan itself** — they are gaps that will block testing or cause different interpretations when QA executes UAT. All are raised so they can be resolved before code is written or tested.

---

## Blocking — Cannot test without these

### QA-P01 — `{date}` format not defined *(assigned to: Owner)*

**User Goal:** Staff reads the message and understands which date their shift is on.

The message template shows `Зміна: {date}` but the format of `{date}` is not specified.

ANSWER: `DD-MM-YYYY` (e.g. `07-04-2026`). Applies to both `{date}` and `{next_date}`.

**Architect note:** Standard `strftime('%d-%m-%Y')`. No locale library needed.

---

### QA-P02 — `{next_time}` not defined *(assigned to: Owner/Architect)*

**User Goal:** Staff knows exactly when their replacement arrives.

The template shows `Наступна зміна: {next_date} о {next_time}` but `{next_time}` is never defined. The plan describes shift start times (Day = 09:00, Night = 17:00, 24h = 09:00) but does not state that `{next_time}` is derived from the next shift's type.

**Question:** Is `{next_time}` the known start time of the next shift type? E.g. if next person is on Night shift → `{next_time}` = `17:00`? Who owns the shift time lookup (config file, hardcoded, other)?

**Answer:** 
Yes, shift time is always same. We have two 24 and night shifts - labor days 9:00 and 17:00, holiday 9:00. 

**Architect decision:** `{next_time}` is a config constant derived from the `day_type` of the next person's date row: `labor` → `17:00`; `holiday` / `other` → `09:00`. No runtime calendar lookup needed. See also QA-P05.

---

### QA-P03 — Edge case: no previous shift *(assigned to: Architect)*

**Technique:** Error Guessing / Boundary Value

Q9 (Sprint 001 ARCH) resolved that `shift_logic.py` returns `None` when no previous shift exists. But the message template always renders:

```
{staff_name} заступає на зміну замість {previous_staff_name}.
```

If `previous_staff_name` is `None`, what does the message say? Options:
- A: `заступає на зміну замість -.` (dash)
- B: The line is omitted entirely
- C: Different sentence ("відкриває зміну" / opens the shift)

Without this defined, QA has no expected result for boundary tests.

**Answer:** If I understand it corectly. We handle corner case of no prevous / next shift with "-" instead of "none" in message.

**Architect decision:** Substitute the string `"-"` into `{previous_staff_name}`. The line is **not omitted** — template structure is unchanged. `shift_logic.py` returns `"-"` (not `None`) for boundary rows.

---

### QA-P04 — Edge case: no next shift *(assigned to: Architect)*

Same as QA-P03 but for the last shift of the period. Does the "Наступна зміна:" block disappear, show a dash, or show a different message?

**Answer:** See above

**Architect decision:** Same rule as QA-P03. For the last shift of the period, `{next_date}`, `{next_time}`, and `{next_staff_name}` all receive `"-"`. Block not omitted.

---

### QA-P05 — Shift type per person per date not defined *(assigned to: Architect)*

**Technique:** State Transition Testing

The shift rule table states that on a `labor` day, **two** shift types occur (Day + Night). But the XLSX grid has **one person per department per date**.

QA cannot determine what shift type to assign to that one person:
- Are they the Day shift person (09:00–17:00)?
- Are they the Night shift person (17:00–09:00)?
- Is there a second row for the same date somewhere?

This affects both `{next_time}` in the message and the entire `shift_logic.py` algorithm.

**Question:** For a given grid cell (department + date), what shift type does that person hold? How does the system determine Day vs Night for the same `labor` date?

**Answer:** 
We have day staff (that works on labor days and duty staff that is on weekend and night. Does it explain sometinhg?

**Architect decision:** The XLSX tracks **duty staff only**. "Day staff" (09:00–17:00, Mon–Fri) are regular employees not included in this notification system. Each grid cell = one duty doctor for that date. Shift type assignment:
- `labor` → Night duty, starts **17:00**
- `holiday` / `other` → 24h duty, starts **09:00**

**Consequence:** The shift rule table in `2026-04-30_Development_Plan.md` was incorrect (showed "Day + Night" per labor day as if both are tracked). Corrected in Dev Plan to reflect duty-only tracking. `{next_time}` = `17:00` when next date is `labor`; `09:00` when `holiday` / `other`. Resolves QA-P02 fully.

---

## Major — Significant gaps in testability

### QA-P06 — Definition of Done: delivery not verifiable *(assigned to: Architect)*

The Definition of Done states: *"All staff in the XLSX receive a correctly formatted Telegram message."*

The `notifications` table records **send attempts**, not confirmed delivery. Telegram API returns 200 OK when the message is queued — not when the user receives it (e.g. blocked bot, deleted account, wrong chat_id all return errors at send time, but a stale chat_id with no active session may silently succeed).

**Question:** Is Owner manual verification on personal devices sufficient for POC? Or is the DoD criterion the DB record of `status='ok'`?

**Answer:** `status='ok' is fine for the moment.

---

### QA-P07 — Name matching between XLSX and contacts.json *(assigned to: Architect)*

**Technique:** Equivalence Partitioning

The plan says parser validates names and reports mismatches. But which is the master source?

- XLSX has: `Єрема В.Р.` (with space) and also `ЦиганокІ.І.` (no space — known formatting issue)
- contacts.json has: names typed by IT Owner

**Question:** When a name in the XLSX does not match any entry in contacts.json — is this a WARNING (skip employee, continue) or ERROR (exit 1)? And which file is the master for correct spelling?

**Architect decision:** Name mismatch between XLSX and `contacts.json` = **WARNING + skip** (log the mismatch, continue processing remaining staff; do not exit 1). `contacts.json` is the **master source** for correct spelling. IT Owner is responsible for keeping both files in sync. At end of run the log reports a total count of skipped names. Consistent with Q14/Q15 decisions (graceful degradation, non-blocking warnings, never silent skips).

---

### QA-P08 — `contacts.json.example` not mentioned *(assigned to: Architect)*

`.env.example` is committed to Git as a template for IT Owner. By the same security/onboarding principle, `contacts.json.example` should also be committed with placeholder values so IT Owner knows the exact format required.

Currently not mentioned in the plan.

**Question:** Should `contacts.json.example` be a committed artifact? Where does it live?

**Answer:** Will appear in development

---

## Minor — Clarifications that improve test precision

### QA-P09 — Q16 header names ✅ CLOSED

Headers are stable export-format constants. Required names are defined in `schedule_parser.py` constants. Parser tests can be written against these constants. TC-PARSER unblocked.

---

### QA-P10 — `contacts.json` not in `.gitignore` — not stated in plan

The plan states contacts.json is "server only, not in Git" but does not state it is added to `.gitignore`. Without a `.gitignore` entry, a developer could accidentally commit it. Security requirement needs an explicit implementation step.

ANSWER: QA to check after development  basic contacts json will appear as a part of project I guess. But with dummy data. 

### QA-P11 — "correctly formatted" needs a measurable definition

Quality Level: Functional Suitability / Correctness says "correctly formatted message — Verified by Owner UAT." This is subjective without a reference. The message template IS defined in the plan — UAT checklist should reference it explicitly as the pass criterion.

Suggest adding to UAT: *"Message received matches the template exactly: date format X, names as in XLSX, shift times as per shift type config."*

ANSWER: no need to be so direct at project level definitions. 

---

## Open items from this review

| ID     | Issue                                             | Assigned to       | Blocking      | Status                  |
|--------|---------------------------------------------------|-------------------|---------------|-------------------------|
| QA-P01 | `{date}` display format                           | Owner             | ✅ Yes         | ✅ Resolved — DD-MM-YYYY |
| QA-P02 | `{next_time}` derivation                          | Owner / Architect | ✅ Yes         | ✅ Resolved — see QA-P05 |
| QA-P03 | No previous shift — message behaviour             | Architect         | ✅ Yes         | ✅ Resolved — show "-"   |
| QA-P04 | No next shift — message behaviour                 | Architect         | ✅ Yes         | ✅ Resolved — show "-"   |
| QA-P05 | One person per date — which shift type?           | Architect         | ✅ Yes         | ✅ Resolved — duty only  |
| QA-P06 | DoD: send attempt vs confirmed delivery           | Owner             | No            | ✅ Resolved — status=ok  |
| QA-P07 | Name mismatch: warning or error?                  | Architect         | No            | ✅ Resolved — WARN+skip  |
| QA-P08 | `contacts.json.example` missing                   | Architect         | No            | ⏳ Dev to add in S002    |
| QA-P09 | Q16 header names unconfirmed                      | Owner             | Yes (tracked) | ✅ Resolved — constants  |
| QA-P10 | `contacts.json` not in `.gitignore`               | Architect         | No            | ⏳ QA to verify post-dev |
| QA-P11 | "correctly formatted" needs measurable definition | Architect         | No            | ✅ Closed — not required |
