# Sprint S006c — Architecture
**Date:** 2026-05-08
**Sprint:** S006c — Pre-filled Constraints + Quality Closure
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

### C3 — Warn when year unreadable (`bot_hook.py`)

Currently: if `year_str` cannot be parsed as integer, `year_int = None` and the entire validator is skipped silently.

New behaviour (silent partial run):
- If `year_int is None`: run validator with `year_int=None` for V1/V2/V3/V5/V7 (these do not need year)
- V4 and V6 are skipped — no warning sent to Head
- No change to the success/warning reply format

Requires small refactor: validator must accept `year_int: int | None` and guard V4/V6 internally instead of the guard living in `bot_hook`.

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

**AD-S006c-003 — year_int guard moves into validator**
The `if year_int is not None` guard in `bot_hook` is replaced by internal guards on V4 and V6 inside `validate_draft_grid`. Signature changes to `year_int: int | None`. This is the correct location — the validator should know which of its checks require year, not the caller.

**AD-S006c-004 — Sheet link uses base URL with tab name as text**
Link format: `https://docs.google.com/spreadsheets/d/{sheet_id} — вкладка '{tab_name}'`. No direct tab anchor (tab anchors require `gid`, unavailable without an extra API call). Tab name appears as readable text so Head knows where to look after clicking.

**AD-S006c-005 — Preferences are soft constraints**
Undesired days deprioritise a staff member for that slot but do not block them. If every eligible candidate for a slot has that day in their undesired list, the algorithm assigns the lowest-shift-count candidate from that group. This prevents empty slots and keeps the algorithm deterministic.

**AD-S006c-006 — Preference column names are configurable**
Column header names are stored in `schedule_mapping.json` under keys `scheduler_preferred_dates_column` and `scheduler_undesired_dates_column`. If a key is absent or the named column is not found in the Staff tab header, preference lists default to empty for all staff — no error, no warning. This keeps backward compatibility with existing sheets that have no preference columns.

**AD-S006c-007 — Preference values: comma-separated integers**
Cell format: `"1, 5, 10"` — comma-separated day-of-month numbers. Non-numeric tokens are silently skipped. This is the simplest format Head can fill manually, and it is also machine-writable when AI normalisation is added in S007. No validation against the actual month length (out of scope for S006c — an out-of-range day is simply never matched).

---

## Modified files

| File                               | Change                                                                              |
|------------------------------------|-------------------------------------------------------------------------------------|
| `schedule_generator.py`            | C1 — skip non-empty cells; count pre-filled staff; C8 — preference-aware selection |
| `bot_hook.py`                      | C2 — append Sheet link; C3 — move year guard, warn on unparseable year              |
| `schedule_validator.py`            | C3 — accept `year_int: int \| None`; guard V4/V6; C4 — skip V2/V3 loop when col missing |
| `google_sheets_adapter.py`         | C7 — read `preferred_dates` and `undesired_dates` columns in `get_staff_list`       |
| `schedule_mapping.json`            | C7 — add `scheduler_preferred_dates_column` and `scheduler_undesired_dates_column`  |
| `tests/test_schedule_validator.py` | C5 — fix T5a assertion; new tests for C3/C4                                         |
| `tests/test_schedule_generator.py` | New tests for C1, C8                                                                |
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
| C3-b | year_int=None — no warning added to reply                                      | C3    | Contract    |
| C3-c | year_int=None — V4/V6 results not in warnings                                  | C3    | Contract    |
| C4   | Missing date column — V3 does not cascade                                      | C4    | Regression  |
| C5   | T5a assertion uses new message text                                            | C5    | Regression  |
| C7-a | Staff record with `preferred_dates` cell — parsed into `preferred_days` list  | C7    | State-based |
| C7-b | Staff record with `undesired_dates` cell — parsed into `undesired_days` list  | C7    | State-based |
| C7-c | Missing or empty preference column — no crash; empty lists returned            | C7    | Contract    |
| C8-a | Preferred day — preferred candidate assigned before neutral candidate          | C8    | Priority    |
| C8-b | Undesired day — neutral candidate assigned before undesired candidate          | C8    | Priority    |
| C8-c | All candidates undesired — slot still filled (soft constraint)                 | C8    | Contract    |

---

## Open questions

| #    | Question                                                        | Needed for | Answer                                       |
|------|-----------------------------------------------------------------|------------|----------------------------------------------|
| OQ-1 | Sheet link format — base URL only, or include tab name as text? | C2    | ✅ Resolved — include tab name as readable text next to the URL          |
| OQ-2 | year_int=None — warn Head, or skip silently?                    | C3    | ✅ Resolved — skip silently; no warning sent to Head                     |
| OQ-3 | Pre-fill counting — count holiday days too, or labour only?     | C1    | ✅ Resolved — all day types                                              |
| OQ-4 | Preferences — per person globally, or can differ per department?    | C7/C8   | Assumption: per person (one row in Staff tab). Owner to confirm if a person can have different preferences when listed under two departments. |
| OQ-5 | Preference column format — comma-separated integers as specified, or another format (date range, named days)? | C7 | ✅ Resolved — comma-separated day-of-month integers (1–31). Out-of-range values silently never match. |

---

## Sign-off

| Role      | Date       | Status                 |
|-----------|------------|------------------------|
| Architect | 2026-05-08 | ⏸ Pending Owner review |
| Developer | —          | ⏸                      |
| QA        | —          | ⏸                      |
| Owner     | —          | ⏸                      |
