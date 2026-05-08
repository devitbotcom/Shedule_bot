# Sprint S006d — Architecture
**Date:** 2026-05-08
**Sprint:** S006d — Preference Data Validation
**Depends on:** S006c accepted

---

## Goal

Detect invalid or conflicting entries in staff preference data before generation runs, warn Head, and exclude affected persons from assignment on the problematic day. Three new checks (V8, V9, V10) close the gap identified in UAT finding 06c-03.

---

## Scope

| In | Out |
|----|-----|
| V8 — warn + exclude when same day is in both preferred and undesired for one person | Blocking generation on V8/V9 data issues |
| V9 — warn when a preference day number is outside the valid range `1…month_length` (catches 0, negatives, and over-length values) | Validating that month length is reachable without year_int |
| V10 — warn + skip preference logic when all staff in a dept share the same preferred day | Cross-department preference conflict detection |
| V9 skipped silently when year_int=None (month length unknown) | Any change to V8/V10 when year_int=None |

---

## Changes

### C1 — V8 and V9: preference data checks (`schedule_validator.py`)

New checks on `staff_list` inside `validate_draft_grid`, running after V7 (name validation).

**V8 — same day in both lists (per person):**
For each staff record, find days where `day ∈ preferred_days AND day ∈ undesired_days`. Emit one warning per conflicting day:
```
[Персонал] '<name>' — день <N> вказано і в бажаних, і в небажаних датах — день пропущено
```

**V9 — out-of-range day number:**
Requires `year_int` and `month_int`. Skip entirely when `year_int is None`. For each staff record, find entries in `preferred_days` or `undesired_days` where `not (1 <= day <= calendar.monthrange(year_int, month_int)[1])`. This covers values above the month length, zero, and negative numbers. Emit one warning per out-of-range entry:
```
[Персонал] '<name>' — бажаний день <N> не існує у місяці — запис проігноровано
[Персонал] '<name>' — небажаний день <N> не існує у місяці — запис проігноровано
```

### C2 — V8 exclusion and V10: generation-time checks (`schedule_generator.py`)

**V8 exclusion:** When building the eligible candidate list for a slot, if `day_number is not None` and `day_number in s.get("preferred_days", [])` and `day_number in s.get("undesired_days", [])` for a candidate, exclude that candidate from the slot entirely (not just demoted to neutral). This is consistent with the validator warning: the day is treated as if it does not exist in either list for that person.

**V10 — all eligible candidates share the same preferred day:**
After the C9 consecutive filter, before applying C8 tiers: if `day_number is not None` and every candidate in `eligible` has `day_number in s.get("preferred_days", [])`, skip the preferred tier (set `preferred = []`, treat all as neutral) and append one warning per affected slot:
```
[Персонал] '<dept>' — день <N> бажаний для всіх лікарів відділення, перевага не застосовується
```

The slot is still filled — this is not a hard block.

---

## Architecture Decisions

**AD-S006d-001 — V8/V9 warnings in validator; V8 exclusion + V10 in generator**
V8 and V9 are staff data quality issues — they belong alongside V7 in `validate_draft_grid`. The exclusion effect of V8 is re-checked inline in `schedule_generator.py` (no need to pass validator output to the generator). V10 is a per-slot check that requires knowing which candidates are eligible at generation time — it lives in the generator.

**AD-S006d-002 — V9 skipped when year_int=None**
Month length cannot be determined without year. When `year_int is None`, V9 is silently skipped. This parallels V4 and V6 behaviour. No extra warning is added (the year-unreadable warning from V4/V6 already covers this).

**AD-S006d-005 — V9 range is `1…month_length`, not just `> month_length`**
Zero and negative integers are syntactically valid (`int("0")`, `int("-1")`) and pass through `_parse_days` unchanged. The condition `not (1 <= day <= max_day)` catches all three invalid cases: below 1, above month length. Non-digit tokens are already rejected by `_parse_days` before reaching the validator.

**AD-S006d-003 — V8 exclusion is per person per day, not per person globally**
A person with day 5 in both lists is excluded only from day 5. All other days proceed normally. The validator warns once per conflicting day per person.

**AD-S006d-004 — V10 is a soft block: slot still filled**
If all eligible staff prefer the same day, preference logic is skipped and the lowest-shift-count candidate is assigned (neutral selection). The slot is never left empty due to V10 alone.

---

## Modified files

| File | Change |
|------|--------|
| `schedule_validator.py` | C1 — V8 and V9 checks after V7 |
| `schedule_generator.py` | C2 — V8 inline exclusion; V10 pre-tier check |
| `tests/test_schedule_validator.py` | New tests for V8/V9 |
| `tests/test_schedule_generator.py` | New tests for V8 exclusion and V10 |

---

## Test plan

| # | Test | Check | Technique |
|---|------|-------|-----------|
| V8-a | Person has day N in both lists → warning `[Персонал]` with day N | V8 validator | Contract |
| V8-b | Person has day N in both lists → not assigned on day N; assigned on other days normally | V8 generator | State-based |
| V8-c | Person has no conflict → no V8 warning (no false positive) | V8 validator | Negative |
| V9-a | Person has day 32 in preferred → warning `[Персонал]` | V9 validator | Contract |
| V9-b | Person has day 32 in undesired → warning `[Персонал]` | V9 validator | Contract |
| V9-c | year_int=None → V9 check skipped, no crash | V9 validator | Edge case |
| V9-d | Person has day 0 in preferred → warning `[Персонал]` | V9 validator | Edge case |
| V9-e | Person has negative day in undesired → warning `[Персонал]` | V9 validator | Edge case |
| V9-f | Valid day within month → no V9 warning (no false positive) | V9 validator | Negative |
| V10-a | All staff in dept prefer same day → warning `[Персонал]` and slot still filled | V10 generator | Contract |
| V10-b | Not all staff prefer same day → preference applied normally, no V10 warning | V10 generator | Negative |

---

## Open questions

| # | Question | Needed for | Answer |
|---|----------|------------|--------|
| OQ-1 | V9 for undesired days: same warning format as preferred? | V9 | ✅ Resolved — same format, label reflects the list: `бажаний` for preferred, `небажаний` for undesired. |

---

## Sign-off

| Role | Date | Status |
|------|------|--------|
| Architect | 2026-05-08 | ✅ ARCH ready |
| Developer | 2026-05-08 | ✅ C1/C2 implemented; D1 fixed; 201/201 tests pass |
| QA | 2026-05-08 | ✅ APPROVED — D1 resolved; 201/201 tests pass |
| Owner | — | ⏸ |
