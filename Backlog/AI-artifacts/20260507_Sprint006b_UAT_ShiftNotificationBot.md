# Sprint S006b — Owner UAT
**Date:** 2026-05-07  
**Sprint:** S006b — Schedule Generation  
**Prepared by:** QA  
**For:** Owner (Myk)

---

## What this sprint delivers

Head can send `/draft` in Telegram and the bot generates a full-month duty schedule using a weighted greedy algorithm, writing the result to a `Draft-by-bot` tab in the Google Sheet.  
The POC1 notification pipeline is untouched.

**Dev/QA sheet (public, no real data):**  
https://docs.google.com/spreadsheets/d/1lKX5ntqGN2UPf9LSDDKJTsGKtHmQiPK2BhtS61OCWv0/edit?usp=sharing

---

## Prerequisites before starting UAT

- [ +] S006a UAT accepted (Google Sheets credentials and `.env` in place)
- [+ ] Service account permission updated from **Viewer** to **Editor** on the Google Sheet
- [+ ] `data/schedule_mapping.json` updated on the server — see Step 6 of `readme_GOOGLE_SHEETS.md` for new key names:
  ```json
  {
    "scheduler_staff_tab":    "Staff",
    "scheduler_schedule_tab": "Draft",
    "scheduler_output_tab":   "Draft-by-bot",
    "scheduler_month_cell":   "A1",
    "scheduler_year_cell":    "B1"
  }
  ```
- [ +] `Draft` tab in the Google Sheet has month name in A1 (Ukrainian, e.g. `травень`), year in B1 (e.g. `2026`), day-type column pre-populated
- [+ ] Head user role assigned: `/setrole <your_telegram_id> head`
- [ +] Latest code pulled and dependencies installed: `cd ~/Shedule_bot && git pull && source venv/bin/activate && pip install -r requirements.txt`

---

## Test cases

### U006b-1 — `/draft` denied for non-Head user

STATUS: ACCEPTED

**Actor:** Owner, as a user without Head role  
**Steps:**
1. Using a Telegram account with `pending` or `staff` role, send `/draft` to the bot

**Expected output:**
```
⛔ Не авторизовано.
```

**Pass criteria:** access denied message received; no schedule generated.

---

### U006b-2 — `/draft` generates schedule and writes Draft-by-bot tab

STATUS: ACCEPTED

**Actor:** Owner, as Head  
**Steps:**
1. Open the Google Sheet, confirm `Draft` tab has month in A1, year in B1, day-type column filled
2. Send `/draft` to the bot from your Head Telegram account

**Expected output (bot reply):**
```
✅ Чернетку розкладу на <місяць> <рік> записано у вкладку 'Draft-by-bot'
```

**Expected state in Google Sheet:**
- `Draft-by-bot` tab created (or overwritten if it existed)
- Each department column contains staff names
- Staff distributed approximately evenly across days

**Pass criteria:** confirmation received; `Draft-by-bot` tab visible in the Sheet with staff assigned.

---

### U006b-3 — `/draft` called twice overwrites previous result

STATUS: QA

**Actor:** Owner, as Head  
**Steps:**
1. Send `/draft` — confirm `Draft-by-bot` tab created
2. Send `/draft` again

**Expected output:** same confirmation message; `Draft-by-bot` tab updated (not duplicated).

**Pass criteria:** only one `Draft-by-bot` tab exists; content reflects latest generation.

---

### U006b-4 — `/help` shows `/draft` for Head

**Actor:** Owner, as Head  
**Steps:**
1. Send `/help` to the bot

**Expected output includes:**
```
/draft — згенерувати чернетку розкладу
```

**Pass criteria:** `/draft` visible in help; not visible for non-Head users.

---

### U006b-5 — POC1 notification pipeline unaffected (regression)

**Steps:**
1. Run:
   ```bash
   cd ~/Shedule_bot && source venv/bin/activate && TZ=Europe/Kyiv python main.py --dry-run
   ```

**Pass criteria:** output identical to pre-S006b behaviour; no errors referencing schedule generation or Google Sheets write.

---

## UAT sign-off

| Case     | Result | Notes |
|----------|--------|-------|
| U006b-1  |        |       |
| U006b-2  |        |       |
| U006b-3  |        |       |
| U006b-4  |        |       |
| U006b-5  |        |       |

**Status:** ⏸ Pending

---

## If something goes wrong

| Symptom                                                            | Where to look                                                                                               |
|--------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| `❌ GOOGLE_SHEET_ID або GOOGLE_SERVICE_ACCOUNT_JSON не налаштовано` | Check `.env` has both variables set                                                                         |
| `❌ Не вдалось прочитати schedule_mapping.json`                     | Check `data/schedule_mapping.json` is valid JSON (no syntax errors)                                         |
| `❌ Невідома назва місяця`                                          | Check cell A1 in the `Draft` tab contains a Ukrainian month name (e.g. `травень`)                           |
| `❌ Не вдалось прочитати дані з Google Sheets`                      | Check service account has **Editor** permission; check `GOOGLE_SHEET_ID`                                    |
| `❌ Не вдалось записати результат`                                  | Check service account has **Editor** (not Viewer) permission                                                |
| `Draft-by-bot` tab empty after generation                          | Check `Draft` tab has day-type column filled; check `scheduler_schedule_tab` key in `schedule_mapping.json` |
| `--dry-run` fails after S006b                                      | Check `schedule.xlsx` and `schedule_mapping.json` notification keys are unchanged                           |

FEEDBACK:

### 06b-01 Bot silent, but it is invisible for support - [HIGH]

Precondition:
IT changed the token, but did not reregister. Or any other issue with setup. 

Actual:
- Bot is silent, but it is invisible for support
- Health command res
> cd ~/Shedule_bot && source venv/bin/activate && python main.py --health
> [TIMEZONE] Europe/Kyiv — 2026-05-07 09:56:02 local
[MAPPING] ❌ cannot parse schedule_mapping.json: Expecting ',' delimiter: line 25 column 5 (char 513)

Explanation i recieved 
``` 
  The bot isn't a daemon — it's invoked by Telegram on each message (CGI/Passenger). So "running" means the webhook is registered and reachable.                                                                           
                                         
  Check webhook status:                                                                                                                                                                                                    
cd ~/Shedule_bot && source venv/bin/activate && python3 -c "import os,json,requests; from dotenv import load_dotenv; load_dotenv('.env');  r=requests.get(f\"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/getWebhookInfo\"); print(json.dumps(r.json(),indent=2))"                                            
  "                                                         
                                                                                                                                                                                                                           
  Key fields to look for:                                   
  - "url" — should be your webhook URL (not empty)                                                                                                                                                                         
  - "last_error_message" — if present, Telegram couldn't reach your endpoint                                                                                                                                               
  - "pending_update_count" — messages waiting to be delivered
```

Expected:
- P1 Logs need to record each hook attempt 
- P2 Integration monitoring dashboard/escalation to IT if system unhealthy.


### 06b-02 lack of visibility with integration failures - [medium]
Actual
```chat
/draft
❌ Не вдалось прочитати місяць/рік з Google Sheets: Draft
```
```console
2026-05-07 21:32:57,298 [INFO] Starting shift_bot | mode=health[CONFIG]   ✅ all variables loaded
[TIMEZONE] Europe/Kyiv — 2026-05-07 21:32:57 local
[SCHEDULE] shift_hours: labor=17:00  holiday=09:00  other=09:44
[ENV TIME]  Thu May  7 14:32:57 EDT 2026
[TZ OFFSET] bot leads server by 7h (Europe/Kyiv EEST UTC+3 vs server EDT UTC-4)
[DB]       ✅ shift_bot.db reachable, schema valid
[TELEGRAM] ✅ bot reachable, token valid
2026-05-07 21:32:57,765 [INFO] Column 'Ургенція спеціалістів на дому' found but skipped (listed in skip_columns)
[XLSX]     ✅ schedule.xlsx found — 8 employees, 6 shift dates
[LAST RUN] no runs recorded yet
[PENDING]  8 shifts pending notification
(venv) [itbomenf@server129 Shedule_bot]$
```

Expected: 
- P1 Health check must include integration with Google
- P2 Logs need to record each hook attempt


###  06b-03 Draft-by-bot content repeats the Draft content [CRITICAL] - DONE

STR  
U006b-2 — `/draft` generates schedule and writes Draft-by-bot tab

Actual:
- Identical content in Draft-by-bot abd Draft.
- some days are empty 
```Spreadsheet
holiday	29	Doc 9
labour	30	
labour	31	Doc 9
```
- some days are repeating same doc
```Spreadsheet
labour	10	Doc 10
labour	11	Doc 10
labour	12	Doc 10
labour	13	Doc 10
holiday	14	Doc 10
holiday	15	Doc 10
```


The distribution algorithm. 
Architect : The algorithm is implemented in S006b — schedule_generator.py with the weighted greedy logic exists and all tests pass.
For each working day, for each department column, the algorithm asks: "which staff member in this department has been assigned the fewest shifts so far?" — and picks that person.

- Greedy — no planning ahead. Each slot is filled immediately with the best local choice, no backtracking.
- Weighted — the "best" choice is defined by a weight: the running shift count per person. Lowest count wins.

to check run 
```bash
cd ~/Shedule_bot && source venv/bin/activate && python3 -c "import os, json; from dotenv import load_dotenv; load_dotenv('.env'); from google_sheets_adapter import get_schedule_grid; mapping = json.load(open('data/schedule_mapping.json')); grid = get_schedule_grid(os.environ['GOOGLE_SHEET_ID'], mapping['scheduler_schedule_tab'], os.environ['GOOGLE_SERVICE_ACCOUNT_JSON']); hr=mapping['header_row'];  print('Sheet headers:', grid[hr-1]); print('Config dept_columns:', mapping['department_columns'])"
```

Actual: 
- The problem is clear. header_row is pointing at a data row (labour, 4, Doc 4) instead of the row that contains the department column names. The algorithm reads that as headers, finds no match with Приймальне
відділення etc., and copies the grid unchanged.

Expected: 
Add separate mapping for cells in scheduler.


### 06b-03 Usability - CR. Add link to google sheet into positive response. - [LOW]
Actual:
✅ Чернетку розкладу на квітень 2026 записано у вкладку 'Draft-by-bot'.

Expected:
✅ Чернетку розкладу на квітень 2026 записано у вкладку 'Draft-by-bot'. <LINK TO NEW TAB IN GOOGLE SHEET>




---

## Known Issues

See `Backlog/backlog_issues.md` — 006b-01, 006b-02.

