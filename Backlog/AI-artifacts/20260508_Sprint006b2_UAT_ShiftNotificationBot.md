# Sprint S006b2 — Owner UAT
**Date:** 2026-05-08
**Sprint:** S006b2 — Draft Validation Warnings
**Prepared by:** QA

---

## What this sprint delivers

After running `/draft`, the bot appends a `⚠️ Попередження:` block to the confirmation message listing any data quality issues found in the Draft tab. Generation always proceeds regardless of warnings.

---

## Prerequisites

- [ ] S006b UAT accepted (scheduler config fixed: `scheduler_header_row`, `scheduler_department_columns` set correctly)
- [ ] Latest code pulled and deps installed: `cd ~/Shedule_bot && git pull && touch tmp/restart.txt`
- [ ] `scheduler_date_column` added to `~/Shedule_bot/data/schedule_mapping.json`

---

## Test cases

### U006b2-1 — Clean draft produces no warnings

**Steps:**
1. Ensure Draft tab has correct day numbers, day-types filled, staff list populated
2. Send `/draft`

**Expected:**
```
✅ Чернетку розкладу на <місяць> <рік> записано у вкладку 'Draft-by-bot'.
```
*(no ⚠️ block)*

**Pass:** confirmation received with no warnings.

---

### U006b2-2 — Warning appears for Sat/Sun not marked holiday

**Steps:**
1. In Draft tab, change day-type of a Saturday or Sunday to `labour`
2. Send `/draft`

**Expected:** confirmation message contains `⚠️ Попередження:` with a line mentioning the day number and `субота` or `неділя`.

**Pass:** warning visible; schedule still generated and written.

---

### U006b2-3 — Warning appears for empty day-type cell

**Steps:**
1. In Draft tab, clear the day-type cell of one row (leave day number filled)
2. Send `/draft`

**Expected:** warning mentions days with missing day-type and `пропущено`.

**Pass:** warning visible; schedule still generated.

---

### U006b2-4 — POC1 regression

**Steps:**
```bash
cd ~/Shedule_bot && source venv/bin/activate && TZ=Europe/Kyiv python main.py --dry-run
```

**Pass:** output identical to pre-S006b2; no errors.

---

## UAT sign-off

| Case | Result | Notes |
|---|---|---|
| U006b2-1 | | |
| U006b2-2 | | |
| U006b2-3 | | |
| U006b2-4 | | |

**Status:** ⏸ Pending
