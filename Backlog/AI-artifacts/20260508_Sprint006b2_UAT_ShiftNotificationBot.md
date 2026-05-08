# Sprint S006b2 — Owner UAT
**Date:** 2026-05-08
**Sprint:** S006b2 — Draft Validation Warnings
**Prepared by:** QA

---

## What this sprint delivers

After running `/draft`, the bot appends a `⚠️ Попередження:` block to the confirmation message listing any data quality issues found in the Draft tab. Generation always proceeds regardless of warnings.

---

## Prerequisites

- [+ ] S006b UAT accepted (scheduler config fixed: `scheduler_header_row`, `scheduler_department_columns` set correctly)
- [ +] Latest code pulled and deps installed: `cd ~/Shedule_bot && git pull && touch tmp/restart.txt`
- [+ ] `scheduler_date_column` added to `~/Shedule_bot/data/schedule_mapping.json`

---

## Test cases

### U006b2-1 — Clean draft produces no warnings
STATUS - ACCEPTED
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

STATUS - Fixed — pending Owner re-run

**Fixes applied:**
- V5 message now reads "після дня {prev} очікувався день {exp}, знайдено {actual}" — day numbers visible in spreadsheet
- Warning block also written to Draft-by-bot tab (not only Telegram)
- V6b added: Mon–Fri marked `holiday` also warns with Ukrainian weekday name

**Steps:**
1. In Draft tab, change day-type of a Saturday or Sunday to `labour`
2. Send `/draft`

**Expected:** confirmation message contains `⚠️ Попередження:` with a line mentioning the day number and `субота` or `неділя`.

**Pass:** warning visible; schedule still generated and written.

---

### U006b2-3 — Warning appears for empty day-type cell

STATUS - Fixed — pending Owner re-run

**Fix applied:** `_cell()` helper added — guards against gspread returning `None` for empty cells (`str(None)` = `"None"` was masking empty values). Column-not-found diagnostic added for misconfigured mapping.

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

| Case     | Result | Notes                                    |
|----------|--------|------------------------------------------|
| U006b2-1 | OK     |                                          |
| U006b2-2 | OK     |             |
| U006b2-3 | OK     |                    |
| U006b2-4 | OK     |                                          |

**Status:** ⏸ Pending Owner re-run of U006b2-2 and U006b2-3

## Feedback:

### 06b2-1 Add also warning if mon-fri is not a labor day [high] - DONE

### 06b2-2 Readability of dates mix up message [high] - DONE
Actual:
• Дні йдуть не по порядку або є пропуски
Expected: 
- add rows, where are the issues, so user can find it easily.
- add warnings listed under content in tab Draft-by-bot, so user can see it not only in the messenger.

### 06b2-3  Failed U006b2-3 [CRITICAL] - DONE
STR: U006b2-3 — Warning appears for empty day-type cell
Actual: No warning values set by scheduler.
Expected: as agreed - warning (as user knows better what is the daytype)

### see 06b-02 lack of visibility with integration failures - [medium] 

### see 06b-01 Bot silent, but it is invisible for support - [HIGH] 

### 06b-03 Usability - CR. Add link to google sheet into positive response. - [LOW] 



