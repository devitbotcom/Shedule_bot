# Sprint S006c — Architecture
**Date:** 2026-05-08
**Sprint:** S006c — Pre-filled Constraints + Quality Closure + UAT Patch (P1–P3)
**Depends on:** S006b2 accepted

---

## Goal

Two goals in one sprint:

1. **Pre-filled constraint support** — if Head has already filled a cell in the Draft tab before running `/draft`, the algorithm leaves it unchanged and counts it toward shift balance. Head can pin any number of assignments before generating the rest algorithmically.
2. **Staff preferences** - Staff tab should have a column (or several) to normalise preferences input. Likely it two: is preferred date, undesired date. later this option will be prepared by genIA after communication with staff and Head. 
3. **Quality closure** — resolve five open backlog items that are too small for their own sprint but should not stay open into S007.

---

## Scope

| In                                                                       | Out                                                                           |
|--------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| Pre-filled cell = constraint: algorithm skips non-empty department cells | Validation that the pre-filled name exists in the Staff tab                   |
| Pre-filled cell counts toward staff shift balance                        | Clearing or overwriting any pre-filled cell                                   |
| Staff tab: two new columns `preferred_dates` and `undesired_dates`       | Hard blocking of staff on undesired days                                      |
| Algorithm uses preferences as soft constraints (deprioritise/prioritise) | AI normalisation of preferences (deferred S007)                               |
| Slot always filled even if all candidates have the day as undesired      | Validation that preference day numbers are valid for the month                |
| Google Sheet link appended to `/draft` success reply                     | Changing the link format based on output tab                                  |
| `/draft` warns Head when year is unreadable (year_int = None)            | Running V4/V6 without year (those two checks require year)                    |
| Fix V3 cascade noise when date column missing                            | Any change to V6 logic                                                        |
| Fix stale T5a test assertion                                             | Any other test changes                                                        |
| `readme_WEBHOOK.md` troubleshooting section                              | New deployment steps                                                          |

---

## Changes

### C1 — Pre-filled cells as constraints (`schedule_generator.py`)

`generate_schedule` currently overwrites every department cell for labour days. New behaviour:

- For each data row × department column: read the current cell value from `template_grid`
- If the cell is **non-empty** after strip: skip it (do not overwrite), but parse the name and increment that person's shift counter so future slots are balanced correctly
- If the cell is **empty**: fill as before (lowest shift count wins)

No new mapping keys. Works with existing `scheduler_department_columns`.

**Pre-fill counting rule:** if the pre-filled value does not match any name in the staff list for that department, increment is skipped silently (the cell is still left unchanged — validation is out of scope here).

### C2 — Google Sheet link in success reply (`bot_hook.py`)

Append a clickable link to the Google Sheet after the confirmation line:

```
✅ Чернетку розкладу на червень 2026 записано у вкладку 'Draft-by-bot'.
🔗 https://docs.google.com/spreadsheets/d/<SHEET_ID> — вкладка 'Draft-by-bot'
```

`sheet_id` and the output tab name are already in scope at the point the reply is built. No new config needed.

### C3 — Warn when year unreadable (`bot_hook.py`) *(updated by UAT P1)*

Currently: if `year_str` cannot be parsed as integer, `year_int = None` and the entire validator is skipped silently.

New behaviour:
- If `year_int is None`: run validator with `year_int=None` for V1/V2/V3/V5/V7 (these do not need year)
- V4 and V6 are skipped
- **One warning appended:** `[Налаштування] рік не вдалось прочитати — перевірки V4 і V6 пропущено`

Requires small refactor: validator must accept `year_int: int | None` and guard V4/V6 internally instead of the guard living in `bot_hook`.

> **UAT P1 (2026-05-08):** Owner reversed OQ-2 during UAT — silent behaviour was confusing. Warning is now mandatory. See AD-S006c-003 (updated).

### C4 — Fix V3 cascade on missing date column (`schedule_validator.py`)

When `day_col_idx is None`, `_cell(row, None)` returns `""` for every row, causing V3 to fire alongside the `[Налаштування]` diagnostic. Fix: skip the V2/V3 collection loop entirely when `day_col_idx is None`.

```python
if day_col_idx is not None:
    for row in data_rows:
        ...  # existing V2/V3/V4/V5 collection
```

V4/V5 also depend on `day_numbers`, so they are naturally skipped too.

### C5 — Fix stale T5a test assertion (`tests/test_schedule_validator.py`)

`test_v4_leap_year_no_warning` checks `not any("має бути" in w ...)` — old message text. Fix:

```python
assert not any("[Структура]" in w and "очікується" in w for w in warnings)
```

### C7 — Staff tab preference columns (`google_sheets_adapter.py`)

Two new optional columns in the Staff tab. Column header names are read from `schedule_mapping.json`:

- Key `scheduler_preferred_dates_column` — header of the "preferred" column (e.g., `"preferred_dates"`)
- Key `scheduler_undesired_dates_column` — header of the "undesired" column (e.g., `"undesired_dates"`)

`get_staff_list` reads these columns and extends each staff record with two new fields:

- `preferred_days: list[int]` — day numbers the person prefers to work
- `undesired_days: list[int]` — day numbers the person prefers not to work

**Parse rule:** split cell value by comma, strip whitespace from each token, convert to `int`, skip non-numeric tokens silently. Empty cell or missing column → empty list (no warning, no crash).

No change to the existing staff record keys. New fields are added alongside the current ones.

### C8 — Preference-aware slot selection (`schedule_generator.py`)

Current: lowest shift count wins per empty slot.

New: three-tier priority for each empty slot, where `day_number` is the spreadsheet day number for that row:

1. **Preferred tier** — candidates where `day_number in staff.preferred_days` — sorted by shift count ascending
2. **Neutral tier** — candidates where the day is in neither list — sorted by shift count ascending
3. **Undesired tier** — candidates where `day_number in staff.undesired_days` — sorted by shift count ascending

Algorithm picks the best candidate from the first non-empty tier. This is a **soft constraint**: if all remaining candidates have the day as undesired, the undesired tier is used anyway — the slot is always filled.

Pre-filled cells (C1) are processed before preference logic runs, so their shift counter increments are already reflected when tier sorting occurs.

### C9 — No-consecutive-day constraint (`schedule_generator.py`) *(UAT P3)*

**Source:** UAT finding 06c-01 — greedy algorithm produced back-to-back shifts for the same person.

The algorithm must not assign the same person on two consecutive calendar days. This is a **hard constraint**: if all candidates for a slot worked the previous calendar day, the slot is left empty and a warning is generated.

**Tracking:** `generate_schedule` maintains `last_day: dict[str, int]` — maps each person's name to the most recent calendar day number they were assigned (across all departments in the same run).

**Selection logic change per slot:**
1. From all candidates (across the three preference tiers), remove anyone whose `last_day[name] == day_number - 1`
2. If remaining candidates exist: apply three-tier preference + shift-count selection as before
3. If **no** remaining candidates (all worked yesterday): leave slot empty; append warning `[День {day_number}] відділення '{dept}' — усі лікарі були на чергуванні вчора, слот залишено порожнім`

**Interface change:** `generate_schedule` now returns a tuple `(grid: list[list], warnings: list[str])`. `bot_hook._cmd_draft` merges generation warnings with validation warnings in the reply and sheet output.

**Edge cases:**
- Day 1 of the grid: `last_day` is empty for everyone → no consecutive penalty → normal selection
- `day_number is None` (unparseable date cell): consecutive check is skipped → normal selection
- Pre-filled cells: `last_day` is **not** updated for pre-fills (the pre-fill date is not tracked)

### C6 — `readme_WEBHOOK.md` troubleshooting section

Add a troubleshooting subsection covering three scenarios encountered during S005 UAT:

1. **"Virtual environment already exists" error** — steps to delete and recreate via cPanel Python App UI
2. **Existing app with wrong domain** — how to remove and reconfigure
3. **Webhook not receiving messages after setup** — check `getWebhookInfo`, confirm URL and secret

---

## Architecture Decisions

**AD-S006c-001 — Pre-fill counts toward balance**
Pre-filled cells are treated as already-assigned shifts. The algorithm reads the name, finds the matching staff record, and increments their counter before filling remaining slots. This prevents the algorithm from assigning that person extra shifts just because it "doesn't know" about the pre-fill.

**AD-S006c-002 — Unknown pre-fill name is ignored for counting**
If the pre-filled name does not match any staff member in the department, shift counting is skipped and the cell is still left unchanged. A warning is out of scope for S006c (would require validator change — deferred to S006d/S008).

**AD-S006c-003 — year_int guard moves into validator; warning mandatory** *(updated UAT P1)*
The `if year_int is not None` guard in `bot_hook` is replaced by internal guards on V4 and V6 inside `validate_draft_grid`. Signature changes to `year_int: int | None`. When `year_int is None`, the validator appends `[Налаштування] рік не вдалось прочитати — перевірки V4 і V6 пропущено`. Owner reversed the "silent" decision (OQ-2) during UAT — Head must be informed when year is unreadable.

**AD-S006c-004 — Sheet link uses base URL with tab name as text**
Link format: `https://docs.google.com/spreadsheets/d/{sheet_id} — вкладка '{tab_name}'`. No direct tab anchor (tab anchors require `gid`, unavailable without an extra API call). Tab name appears as readable text so Head knows where to look after clicking.

**AD-S006c-005 — Preferences are soft constraints**
Undesired days deprioritise a staff member for that slot but do not block them. If every eligible candidate for a slot has that day in their undesired list, the algorithm assigns the lowest-shift-count candidate from that group. This prevents empty slots and keeps the algorithm deterministic.

**AD-S006c-006 — Preference column names are configurable**
Column header names are stored in `schedule_mapping.json` under keys `scheduler_preferred_dates_column` and `scheduler_undesired_dates_column`. If a key is absent or the named column is not found in the Staff tab header, preference lists default to empty for all staff — no error, no warning. This keeps backward compatibility with existing sheets that have no preference columns.

**AD-S006c-007 — Preference values: comma-separated integers**
Cell format: `"1, 5, 10"` — comma-separated day-of-month numbers. Non-numeric tokens are silently skipped. This is the simplest format Head can fill manually, and it is also machine-writable when AI normalisation is added in S007. No validation against the actual month length (out of scope for S006c — an out-of-range day is simply never matched).

**AD-S006c-008 — No-consecutive is a hard constraint with warning** *(UAT P3)*
Owner decision (OQ-6): if all candidates for a slot worked the previous calendar day, the slot is left **empty** — no assignment is forced. A warning is appended so Head can fill the gap manually. An empty slot is preferable to an unknown back-to-back shift that Head may not notice. `generate_schedule` returns `(grid, warnings)` to surface these gaps.

**AD-S006c-009 — Preference column names are fully user-defined via mapping** *(UAT P2 clarification)*
`scheduler_preferred_dates_column` and `scheduler_undesired_dates_column` in `schedule_mapping.json` must be set to whatever column headers the Owner uses in their Staff tab. No default value is assumed. The `schedule_mapping.json.example` uses Ukrainian names (`"бажано"`, `"не бажано"`) purely as illustration — the Owner chooses their own names. Confirmed during UAT: Owner expected this to work like `scheduler_department_columns`.

---

## Modified files

| File                               | Change                                                                              |
|------------------------------------|-------------------------------------------------------------------------------------|
| `schedule_generator.py`            | C1 — skip non-empty cells; count pre-filled staff; C8 — preference-aware selection; C9 — no-consecutive hard constraint; return `(grid, warnings)` |
| `bot_hook.py`                      | C2 — append Sheet link; C3 — move year guard, warn on unparseable year; C9 — merge generation warnings into reply |
| `schedule_validator.py`            | C3 — accept `year_int: int \| None`; guard V4/V6; warn when None; C4 — skip V2/V3 loop when col missing |
| `google_sheets_adapter.py`         | C7 — read preference columns in `get_staff_list`                                    |
| `schedule_mapping.json.example`    | C9/P2 — update preference column example values to Ukrainian; add explanatory comment |
| `tests/test_schedule_validator.py` | C5 — fix T5a assertion; new tests for C3/C4 (including C3-b: warning present)       |
| `tests/test_schedule_generator.py` | New tests for C1, C8, C9                                                            |
| `tests/test_cmd_draft.py`          | New tests for C2/C3                                                                 |
| `readme_WEBHOOK.md`                | C6 — troubleshooting section                                                        |

---

## Test plan additions

| #    | Test                                                                           | Check | Technique   |
|------|--------------------------------------------------------------------------------|-------|-------------|
| C1-a | Pre-filled cell not overwritten                                                | C1    | Regression  |
| C1-b | Pre-filled cell counted in balance (filled person gets fewer additional slots) | C1    | State-based |
| C1-c | Unknown pre-fill name — cell unchanged, no crash                               | C1    | Contract    |
| C2   | Sheet link present in success reply                                            | C2    | EP          |
| C3-a | year_int=None — V1/V2/V3/V5/V7 still run, no crash                            | C3    | Negative    |
| C3-b | year_int=None — [Налаштування] warning present in warnings list                | C3    | Contract    |
| C3-c | year_int=None — V4/V6 results not in warnings                                  | C3    | Contract    |
| C4   | Missing date column — V3 does not cascade                                      | C4    | Regression  |
| C5   | T5a assertion uses new message text                                            | C5    | Regression  |
| C7-a | Staff record with `preferred_dates` cell — parsed into `preferred_days` list  | C7    | State-based |
| C7-b | Staff record with `undesired_dates` cell — parsed into `undesired_days` list  | C7    | State-based |
| C7-c | Missing or empty preference column — no crash; empty lists returned            | C7    | Contract    |
| C8-a | Preferred day — preferred candidate assigned before neutral candidate          | C8    | Priority    |
| C8-b | Undesired day — neutral candidate assigned before undesired candidate          | C8    | Priority    |
| C8-c | All candidates undesired — slot still filled (soft constraint)                 | C8    | Contract    |
| C9-a | Candidate worked yesterday — not assigned today when alternative exists        | C9    | Priority    |
| C9-b | All candidates worked yesterday — slot left empty, warning generated           | C9    | Contract    |
| C9-c | Day 1 — no consecutive penalty applied (last_day empty)                        | C9    | Edge case   |
| C9-d | generate_schedule returns (grid, warnings) tuple                               | C9    | Interface   |

---

## Open questions

| #    | Question                                                        | Needed for | Answer                                       |
|------|-----------------------------------------------------------------|------------|----------------------------------------------|
| OQ-1 | Sheet link format — base URL only, or include tab name as text? | C2    | ✅ Resolved — include tab name as readable text next to the URL          |
| OQ-2 | year_int=None — warn Head, or skip silently?                    | C3    | ✅ Resolved — **always warn** (reversed during UAT 2026-05-08): `[Налаштування] рік не вдалось прочитати — перевірки V4 і V6 пропущено` |
| OQ-3 | Pre-fill counting — count holiday days too, or labour only?     | C1    | ✅ Resolved — all day types                                              |
| OQ-4 | Preferences — per person globally, or can differ per department?    | C7/C8   | Assumption: per person (one row in Staff tab). Owner to confirm if a person can have different preferences when listed under two departments. |
| OQ-5 | Preference column format — comma-separated integers as specified, or another format (date range, named days)? | C7 | ✅ Resolved — comma-separated day-of-month integers (1–31). Out-of-range values silently never match. |
| OQ-6 | No-consecutive constraint: hard block (empty slot + warn) or soft (fill anyway)? | C9 | ✅ Resolved — **hard block + warning** (Owner decision 2026-05-08). Empty slot is preferable; Head fills gap manually. |
| OQ-7 | Preference column names: fix to Ukrainian defaults or fully configurable via mapping? | C7/P2 | ✅ Resolved — **fully configurable** via mapping keys, same pattern as `scheduler_department_columns`. Example shows Ukrainian names as illustration only. |

---

## Deferred to S006d

Raised during S006c UAT (finding 06c-03). Owner confirmed rule: **detect invalid/conflicting preference entry → exclude that person from assignment on the affected day → warn Head.** Three new validator checks on the staff list:

### V8 — Same day in both preferred and undesired (per person)
**Condition:** `day ∈ preferred_days AND day ∈ undesired_days` for the same person.  
**Action:** exclude that person from assignment on that day; treat as if the day is absent from both lists.  
**Warning:** `[Персонал] '<name>' — день <N> вказано і в бажаних, і в небажаних датах — день пропущено`

### V9 — Day number out of valid range
**Condition:** any integer in `preferred_days` or `undesired_days` that exceeds the actual month length.  
**Action:** drop the out-of-range entry; it can never match a real row.  
**Warning:** `[Персонал] '<name>' — бажаний день <N> не існує у місяці — запис проігноровано`  
*(same format for undesired)*

### V10 — All staff in a department share the same preferred day
**Condition:** every candidate for a given department has the same day in their `preferred_days`.  
**Action:** skip preference logic for that day in that department (all candidates treated as neutral).  
**Warning:** `[Персонал] <dept> — день <N> бажаний для всіх лікарів відділення, перевага не застосовується`

**Implementation note:** V8 and V9 run on the staff list before generation (same phase as V1/V7). V10 runs per department per day during generation. Owner decision recorded 2026-05-08.

---

## Sign-off

| Role      | Date       | Status                                              |
|-----------|------------|-----------------------------------------------------|
| Architect | 2026-05-08 | ✅ ARCH accepted; UAT patch P1–P3 designed; V8/V9/V10 recorded for S006d |
| Developer | 2026-05-08 | ✅ P1–P3 implemented; 187/187 tests pass             |
| QA        | 2026-05-08 | ✅ 187/187 tests pass; all 19 ARCH test cases covered |
| Owner     | —          | ⏸ UAT re-test pending — U006c-2/3/4 IN RE-TEST      |
