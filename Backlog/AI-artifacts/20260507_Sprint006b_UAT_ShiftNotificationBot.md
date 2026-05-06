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

- [ ] S006a UAT accepted (Google Sheets credentials and `.env` in place)
- [ ] Service account permission updated from **Viewer** to **Editor** on the Google Sheet
- [ ] `data/schedule_mapping.json` updated on the server — see Step 6 of `readme_GOOGLE_SHEETS.md` for new key names:
  ```json
  {
    "scheduler_staff_tab":    "Staff",
    "scheduler_schedule_tab": "Draft",
    "scheduler_output_tab":   "Draft-by-bot",
    "scheduler_month_cell":   "A1",
    "scheduler_year_cell":    "B1"
  }
  ```
- [ ] `Draft` tab in the Google Sheet has month name in A1 (Ukrainian, e.g. `травень`), year in B1 (e.g. `2026`), day-type column pre-populated
- [ ] Head user role assigned: `/setrole <your_telegram_id> head`
- [ ] Latest code pulled and dependencies installed: `cd ~/Shedule_bot && git pull && source venv/bin/activate && pip install -r requirements.txt`

---

## Test cases

### U006b-1 — `/draft` denied for non-Head user

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

| Symptom | Where to look |
|---------|---------------|
| `❌ GOOGLE_SHEET_ID або GOOGLE_SERVICE_ACCOUNT_JSON не налаштовано` | Check `.env` has both variables set |
| `❌ Не вдалось прочитати schedule_mapping.json` | Check `data/schedule_mapping.json` is valid JSON (no syntax errors) |
| `❌ Невідома назва місяця` | Check cell A1 in the `Draft` tab contains a Ukrainian month name (e.g. `травень`) |
| `❌ Не вдалось прочитати дані з Google Sheets` | Check service account has **Editor** permission; check `GOOGLE_SHEET_ID` |
| `❌ Не вдалось записати результат` | Check service account has **Editor** (not Viewer) permission |
| `Draft-by-bot` tab empty after generation | Check `Draft` tab has day-type column filled; check `scheduler_schedule_tab` key in `schedule_mapping.json` |
| `--dry-run` fails after S006b | Check `schedule.xlsx` and `schedule_mapping.json` notification keys are unchanged |
