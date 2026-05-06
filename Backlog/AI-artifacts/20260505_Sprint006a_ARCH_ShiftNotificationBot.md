# Sprint S006a — Architecture

**Sprint:** S006a  
**Role:** Architect  
**Date:** 2026-05-05  
**Status:** ⏸ READY FOR DEVELOPER  
**Depends on:** S005 UAT accepted  
**Blocks:** S006b (schedule generation)

---

## Sprint Goal

Bot can read the staff list and schedule grid from a designated Google Sheet. Both serve the scheduling process (S006b+). The notification pipeline (POC1) is a fully separate, independent process — this sprint has no connection to it.

**Dev/QA sheet (public, no real data):** https://docs.google.com/spreadsheets/d/1lKX5ntqGN2UPf9LSDDKJTsGKtHmQiPK2BhtS61OCWv0/edit?usp=sharing  
**Production:** authenticated access — defined later.

---

## Scope

| In                                                                            | Out                                                  |
|-------------------------------------------------------------------------------|------------------------------------------------------|
| Read staff list from named Google Sheet tab (feeds S006b)                     | Writing to local `schedule.xlsx`                     |
| Read schedule grid from named Google Sheet tab (scheduling process input)     | CLI flag `--sync-schedule`                           |
| Service account authentication — dev/QA                                       | Any connection to notification pipeline              |
| Tests: adapter (no live API calls)                                            | Authenticated access for prod (defined later)        |
|                                                                               | Modifying the Google Sheet                           |
|                                                                               | Google Drive write-back                              |
|                                                                               | OAuth user-facing flow                               |

> **Note:** `schedule_sync.py` and `--sync-schedule` were built during this sprint on the wrong assumption that scheduling output feeds the notification pipeline. They are out of scope for POC2. The code is harmless but not used.

---

## Key Architectural Decisions

### AD-S006a-001 — `gspread` as Google Sheets client

Use the `gspread` library (Google Sheets API v4 wrapper). Service account authentication — no user interaction, suitable for server-side execution. Credentials stored as a JSON key file; path in `.env` as `GOOGLE_SERVICE_ACCOUNT_JSON`. The sheet is identified by `GOOGLE_SHEET_ID` in `.env`.

**IT setup required (one-time):**
1. Create a Google Cloud project
2. Enable Google Sheets API
3. Create a service account and download the JSON key
4. Share the Google Sheet with the service account email (Viewer permission)
5. Set `GOOGLE_SERVICE_ACCOUNT_JSON` and `GOOGLE_SHEET_ID` in `.env`

---

### AD-S006a-002 — Tab names in `schedule_mapping.json`

Two new keys added to `data/schedule_mapping.json`:

```json
{
  "staff_tab": "Staff",
  "schedule_tab": "Schedule"
}
```

Tab names are IT-configurable without touching code. Same single-source-of-truth principle as `shift_hours`.

---

### AD-S006a-003 — `google_sheets_adapter.py` interface

New file `google_sheets_adapter.py`. Exposes two functions:

```python
def get_staff_list(sheet_id: str, tab_name: str, credentials_path: str) -> list[dict]:
    """Returns list of {name, department} dicts from the staff tab."""

def get_schedule_grid(sheet_id: str, tab_name: str, credentials_path: str) -> list[list]:
    """Returns all cell values as a 2D list — same raw shape as openpyxl iter_rows."""
```

`get_staff_list` feeds the S006b generation algorithm. `get_schedule_grid` reads the schedule from Google Sheets as input to the scheduling process — no connection to the notification pipeline.

---

### AD-S006a-004 — `schedule_sync.py` ❌ OUT OF SCOPE

Built on the wrong assumption that scheduling output feeds the notification pipeline. Removed from scope. Code exists in repo but is not used in POC2.

---

### AD-S006a-005 — `--sync-schedule` CLI flag ❌ OUT OF SCOPE

Built alongside AD-S006a-004 on the same wrong assumption. Removed from scope. Code exists in repo but is not used in POC2.

---

### AD-S006a-006 — Credentials never in git

`GOOGLE_SERVICE_ACCOUNT_JSON` points to an absolute path on the server (e.g. `/home/itbomenf/Shedule_bot/data/service_account.json`). The `data/` directory is already in `.gitignore` (`data/*`). No additional ignore rules needed.

---

## Developer Deliverables

| #  | Deliverable           | File(s)                                                              | Notes                                                       |
|----|-----------------------|----------------------------------------------------------------------|-------------------------------------------------------------|
| D1 | Google Sheets adapter | `google_sheets_adapter.py`                                           | `get_staff_list`, `get_schedule_grid`; `gspread` dependency |
| D2 | ~~Schedule sync~~     | ~~`schedule_sync.py`~~                                               | ❌ Out of scope — wrong assumption                          |
| D3 | ~~CLI flag~~          | ~~`cli.py`, `main.py`~~                                              | ❌ Out of scope — wrong assumption                          |
| D4 | Config additions      | `.env.example`                                                       | `GOOGLE_SHEET_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON`            |
| D5 | Mapping additions     | `data/schedule_mapping.json.example`                                 | `staff_tab`, `schedule_tab` keys                            |
| D6 | Dependency            | `requirements.txt`                                                   | Add `gspread`                                               |
| D7 | Tests                 | `tests/test_google_sheets_adapter.py`                                | Mock `gspread`; no live API calls                           |

---

## Refactor Required (2026-05-06)

D2 and D3 were built on a wrong assumption and must be removed from the codebase.

**Delete files:**
- `schedule_sync.py`
- `tests/test_schedule_sync.py`

**Edit `cli.py`:**
- Remove `--sync-schedule` argument
- Remove `args.sync_schedule` from `_admin_modes`
- Remove `elif args.sync_schedule: mode = "sync_schedule"` branch
- Fix stale error message on `_admin_modes` guard (QA finding F1): text still names only `--register-webhook` and `--bootstrap-it`

**Edit `main.py`:**
- Remove `elif run_mode.mode == "sync_schedule":` dispatch block

**Edit `models.py`:**
- Remove `sync_schedule` from `mode` docstring

**Keep everything else** — `google_sheets_adapter.py`, `tests/test_google_sheets_adapter.py`, `requirements.txt` (`gspread`), `.env.example` additions, `data/schedule_mapping.json.example` additions are all correct and in scope.

---

## Staff Tab — Expected Google Sheet Structure

| Column       | Content                                    |
|--------------|--------------------------------------------|
| `Name`       | Full name of staff member                  |
| `Department` | Department identifier matching XLSX header |

Exact column names are constants in `google_sheets_adapter.py` (same convention as `schedule_parser.py` required headers).

---

## Open Questions

| #    | Question                                                | Needed for | Status |
|------|---------------------------------------------------------|------------|--------|
| OQ-1 | Exact column names in the staff tab of the Google Sheet | D1         | ✅ Confirmed: `Name`, `Department` |

---

## Sprint Sign-off

| Role      | Date       | Status                |
|-----------|------------|-----------------------|
| Architect | 2026-05-06 | ✅ Refactor instructions added — ready for Developer |
| Developer | —          | ⏸ Refactor required                                 |
| QA        | —          | ⏸                                                   |
| Owner     | —          | ⏸                                                   |
