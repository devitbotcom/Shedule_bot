# Sprint S006c — Owner UAT
**Date:** 2026-05-08
**Sprint:** S006c — Pre-filled Constraints + Staff Preferences + Quality Closure
**Prepared by:** QA

---

## What this sprint delivers

1. **Pre-filled constraints** — cells you fill manually in the Draft tab before `/draft` are preserved and counted toward shift balance.
2. **Staff preferences** — optional `preferred_dates` / `undesired_dates` columns in the Staff tab influence who gets assigned to each day (soft constraint — slot always filled).
3. **Sheet link in reply** — `/draft` success message now includes a clickable link to the Google Sheet.
4. **Warning when year unreadable** — if the year cell cannot be parsed, a warning `[Налаштування] рік не вдалось прочитати — перевірки V4 і V6 пропущено` is sent to Head; checks that do not need year (V1/V2/V3/V5/V7) still run.
5. **V3 cascade fix** — missing date column no longer produces a false "rows without day number" warning alongside the config warning.
6. **readme_WEBHOOK.md** — three new troubleshooting scenarios added.

---

## Prerequisites

- [ +] S006b2 UAT accepted
- [ +] Latest code pulled on server:
  ```bash
  cd ~/Shedule_bot && git pull && touch tmp/restart.txt
  ```
- [ +] `scheduler_date_column` already set in `~/Shedule_bot/data/schedule_mapping.json` (from S006b2)
- [ +] Draft tab populated with a valid month grid (day numbers + day-types)
- [ +] Staff tab populated with at least two staff per department

---

## Test cases

---

### U006c-1 — Sheet link appears in `/draft` success reply

STATUS : ACCEPTED

**Tests:** C2

**Steps:**
1. Send `/draft` to the bot (Draft tab must be valid — no issues needed)

**Expected reply:**
```
✅ Чернетку розкладу на <місяць> <рік> записано у вкладку 'Draft-by-bot'.
🔗 https://docs.google.com/spreadsheets/d/<YOUR_SHEET_ID> — вкладка 'Draft-by-bot'
```

**Pass:** reply contains a `docs.google.com/spreadsheets/d/` link and the tab name `'Draft-by-bot'`.

---

### U006c-2 — Pre-filled cell preserved and counted; no back-to-back shifts

STATUS : IN RE-TEST *(06c-01 fixed by P3 — no-consecutive constraint implemented)*

**Tests:** C1, C9

**Steps:**
1. In the **Draft tab**, manually type the name of one of your staff into a department cell for one specific day (e.g. put "Іваненко І.І." in the Surgery column for day 5)
2. Leave all other department cells empty
3. Send `/draft`
4. Open the `Draft-by-bot` tab in Google Sheets

**Expected:**
- The cell you filled is **unchanged** in `Draft-by-bot`
- That staff member appears **fewer times** in other days of the same department as colleagues (because their one pre-filled shift was counted toward the balance)
- No staff member is assigned on two consecutive calendar days (e.g. if someone is on day 5, they will not appear on day 6 in any department)
- If all staff for a department worked the previous day, that slot is left empty and a warning appears in the reply and in the sheet

**Pass:** pre-filled cell preserved; staff member not over-assigned relative to colleagues; no back-to-back shifts.

---

### U006c-3 — Staff preferences (optional — requires Staff tab setup)

STATUS : IN RE-TEST *(06c-02 resolved by P2 — column names are now fully user-defined via mapping; 06c-03 deferred to S006d)*

**Tests:** C7, C8

> **Setup required before this test:**
>
> 1. Add two columns to your **Staff tab** — name them whatever you like (e.g. `"бажано"` and `"не бажано"`).
> 2. For one staff member, enter day numbers in the "preferred" column (e.g. `"1, 5, 10"`).
> 3. For a different staff member in the same department, enter the same days in the "undesired" column.
> 4. Add these two lines to `~/Shedule_bot/data/schedule_mapping.json`, using **your exact column header names**:
>    ```json
>    "scheduler_preferred_dates_column": "бажано",
>    "scheduler_undesired_dates_column": "не бажано"
>    ```
> 5. Restart the app: `touch ~/Shedule_bot/tmp/restart.txt`

**Steps:**
1. Send `/draft`
2. Open `Draft-by-bot` tab
3. Check days 1, 5, and 10 for the department where you set preferences

**Expected:**
- On days 1, 5, 10 — the staff member with those days as preferred is assigned **more often** than the one with those same days as undesired
- All slots are filled (no empty department cells on any day)

**Pass:** preference is visibly respected; no empty slots.

> **Note on 06c-03:** warnings for invalid preference data (same day in both lists, out-of-range day number, conflicting preferences across staff) are **deferred to S006d**. The algorithm silently ignores out-of-range values and applies the soft constraint when data is valid.

---

### U006c-4 — Invalid year in sheet — warning sent to Head, no crash

STATUS : IN RE-TEST *(P1 implemented — bot now warns when year is unreadable)*

**Tests:** C3

**Steps:**
1. In the **Draft tab**, temporarily change the year cell (normally cell B1) to something that is not a number, e.g. `"???"`
2. Send `/draft`
3. Restore the year cell to the correct year

**Expected:**
- Bot replies with ✅ success
- Reply **contains** a warning: `[Налаштування] рік не вдалось прочитати — перевірки V4 і V6 пропущено`
- No crash; other validation checks (V1/V2/V3/V5/V7) still run normally

**Pass:** success reply received; year-unreadable warning is visible in the reply.



---

### U006c-5 — POC1 regression

STATUS : PASSED

**Steps:**
```bash
cd ~/Shedule_bot && source venv/bin/activate && TZ=Europe/Kyiv python main.py --dry-run
```

**Pass:** output identical to pre-S006c; no errors.

---

### U006c-6 — readme_WEBHOOK.md readable (documentation check)

STATUS : PASSED

**Steps:**
1. Open `~/Shedule_bot/readme_WEBHOOK.md` (or view on GitHub)
2. Scroll to the **Troubleshooting** section

**Expected:** three new subsections present:
- "Virtual environment already exists" error during setup
- Existing app configured for wrong domain
- Webhook registered but bot not receiving messages

**Pass:** all three sections visible with concrete fix steps.

---

## QA notes for Owner

| Finding                                                    | Severity | Impact on UAT |
|------------------------------------------------------------|----------|---------------|
| F1 — V2/V3/V5/V7 not explicitly tested under year_int=None | Low | None — behavior correct, U006c-4 covers the user-visible contract |
| F3 — KI-003 and KI-004 not closed in KI doc                | Low | None — both resolved by C3; docs need cleanup post-UAT |
| OB-1 — Generation warnings (C9 slot-empty) not individually logged to webhook.log | Low | None — warnings visible in reply and sheet; no user impact |
| OB-2 — last_day constraint is cross-department (same person blocked across all depts the next day) | Info | By design per AD-S006c-008; only matters if one person covers multiple departments simultaneously |

---

## UAT sign-off

| Case     | Result        | Notes                                                          |
|----------|---------------|----------------------------------------------------------------|
| U006c-1  | PASSED        |                                                                |
| U006c-2  | IN RE-TEST    | 06c-01 fixed by P3 (no-consecutive constraint)                 |
| U006c-3  | IN RE-TEST    | 06c-02 fixed by P2 (configurable column names); 06c-03 → S006d |
| U006c-4  | IN RE-TEST    | P1 implemented — bot now warns when year is unreadable         |
| U006c-5  | PASSED        |                                                                |
| U006c-6  | PASSED        |                                                                |

**Status:** ⏸ Pending Owner re-test of U006c-2, U006c-3, U006c-4


FEEDBACK:

### 06c-01 plain distribution leads to repeating shifts [CRITICAL]
STR:  U006c-2
```spleadsheet
1	
2	Перший Ф.Я
3	Друга ДУ
4	Третій Л. А.
5	Четвертий В. В.В.
```
Actual: Content preserved (as expected), but the staff distribution is not valid (same person two days in a row).
Expected: human friendly distribution of duties.

### 06c-02 preferred dates must be in mapping not hardcoded [HIGH]
STR: U006c-3 
Actual: user sees tech data.
Expected: user expects his native language e.g. 'бажано','не бажано'

### 06c-03  
Precondition: 
```spreadsheet Staff
Перший Ф.Я	Приймальне відділення		1,4
Друга ДУ	Приймальне відділення	1,15	
Третій Л. А.	Приймальне відділення	5	5
Четвертий В. В.В.	Приймальне відділення	32	
Біль В.А.	Анестезіологія	1	2
Морфеус А.А.	Анестезіологія	1	2
```
Data was set intentionally!

STR: U006c-3 

Actual:
- No warning about "Третій Л. А.	Приймальне відділення	5	5" impossible statement
- No warning about "Четвертий В. В.В.	Приймальне відділення	32" inappropriate day number
- No warning about "Біль В.А.	Анестезіологія	1	2; Морфеус А.А.	Анестезіологія	1	2" conflicting statement 

Expected: 
User friendly warning. Distribute only for nonconflicting dates.

The solution is owerfit, 
WHY SO COMPLEX!?
- Just skip a day that in conflict DO NOT make desisions for user
e.g. • [Персонал] 'Анестезіологія' — день 1 бажаний для всіх лікарів відділення, перевага не застосовується
  • [Персонал] 'Третій Л. А.' — день 22 вказано і в бажаних, і в небажаних датах — день пропущено
it should just keep days blank!
