# Sprint S006a — Owner UAT
**Date:** 2026-05-06  
**Sprint:** S006a — Google Sheets Integration  
**Prepared by:** QA  
**For:** Owner (Myk)

---

## What this sprint delivers

The bot can now read the staff list and schedule grid from a designated Google Sheet.  
These are the building blocks for S006b (schedule generation algorithm).  
The POC1 notification pipeline is untouched and unchanged.

**Dev/QA sheet (public, no real data):**  
https://docs.google.com/spreadsheets/d/1lKX5ntqGN2UPf9LSDDKJTsGKtHmQiPK2BhtS61OCWv0/edit?usp=sharing

---

## Prerequisites before starting UAT

- [+ ] Latest code pulled and dependencies installed: `cd ~/Shedule_bot && git pull && source venv/bin/activate && pip install -r requirements.txt`
- [ ] Google Sheets integration configured — follow [readme_GOOGLE_SHEETS.md](../../readme_GOOGLE_SHEETS.md) Steps 1–6

If prerequisites are not yet done, complete them first — UAT cannot proceed without credentials and sheet access.

---

## Test cases

### U006a-1 — Read staff list from Google Sheets

**Actor:** Owner, on the server via SSH or cPanel Terminal  
**Steps:**
1. Run:
   ```bash
   cd ~/Shedule_bot && source venv/bin/activate && python3 -c "
   import os, sys
   from dotenv import load_dotenv
   load_dotenv('.env')
   from google_sheets_adapter import get_staff_list
   staff = get_staff_list(os.environ['GOOGLE_SHEET_ID'], 'Staff', os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])
   print(f'Staff rows: {len(staff)}')
   for s in staff[:3]: print(s)
   "
   ```

**Expected output:**
```
Staff rows: <number>
{'name': '...', 'department': '...'}
...
```

**Pass criteria:** at least one staff row returned; each row has `name` and `department` keys; no exception.

---

### U006a-2 — Read schedule grid from Google Sheets

**Steps:**
1. Run:
   ```bash
   cd ~/Shedule_bot && source venv/bin/activate && python3 -c "
   import os
   from dotenv import load_dotenv
   load_dotenv('.env')
   from google_sheets_adapter import get_schedule_grid
   rows = get_schedule_grid(os.environ['GOOGLE_SHEET_ID'], 'Schedule', os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])
   print(f'Schedule rows: {len(rows)}')
   if rows: print('First row:', rows[0])
   "
   ```

**Expected output:**
```
Schedule rows: <number>
First row: [...]
```

**Pass criteria:** grid returned as a list of rows; first row visible; no exception.

---

### U006a-3 — Wrong credentials fail cleanly

**Steps:**
1. Temporarily set `GOOGLE_SERVICE_ACCOUNT_JSON=/nonexistent/path.json` in `.env`
2. Run the U006a-1 command again
3. Restore the correct path in `.env`

**Expected output:** exception or error message from gspread; no crash that affects other bot functions.

**Pass criteria:** error is raised and visible; does not affect the notification pipeline.

---

### U006a-4 — POC1 notification pipeline unaffected (regression)

**Steps:**
1. Run:
   ```bash
   cd ~/Shedule_bot && source venv/bin/activate && TZ=Europe/Kyiv python main.py --dry-run
   ```

**Pass criteria:** output identical to pre-S006a behaviour; no errors referencing Google Sheets or gspread.

---

## UAT sign-off

| Case     | Result | Notes |
|----------|--------|-------|
| U006a-1  |        |       |
| U006a-2  |        |       |
| U006a-3  |        |       |
| U006a-4  |        |       |

**Status:** ⏸ Pending

---

## If something goes wrong

| Symptom                                          | Where to look                                                                                 |
|--------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `ModuleNotFoundError: No module named 'gspread'` | Run `pip install -r requirements.txt` in venv                                                 |
| `FileNotFoundError` on credentials path          | Check `GOOGLE_SERVICE_ACCOUNT_JSON` in `.env` is an absolute path                             |
| `gspread.exceptions.SpreadsheetNotFound`         | Check `GOOGLE_SHEET_ID` in `.env`; verify sheet is shared with service account email          |
| `gspread.exceptions.WorksheetNotFound`           | Check `staff_tab` / `schedule_tab` in `schedule_mapping.json` match actual tab names in Sheet |
| `--dry-run` fails after S006a                    | Check `schedule.xlsx` and `schedule_mapping.json` are unchanged                               |


## FEEDBACK

### 06-01 
Actual 

```json
{
  "staff_tab": "Staff",
  "schedule_tab": "Schedule"
}
```

Expected - more descriptive settings variables. 
Can it be 

```json
{
  "scheduler_staff_tab": "Staff",
  "scheduler_schedule_tab": "Draft"
}
```