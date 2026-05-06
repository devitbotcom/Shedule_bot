# Sprint S006a — Developer Handoff Artifact
**Date:** 2026-05-05  
**Sprint:** S006a — Google Sheets Integration  
**Status:** ⚠️ REFACTOR REQUIRED — see Architect input 2026-05-06

---

## Deliverables completed

| ID  | Deliverable               | File(s)                                                               | Status |
|-----|---------------------------|-----------------------------------------------------------------------|--------|
| D1  | Google Sheets adapter     | `google_sheets_adapter.py`                                            | ✅     |
| D2  | ~~Schedule sync~~         | ~~`schedule_sync.py`~~                                                | ❌ Out of scope — to be deleted |
| D3  | ~~CLI flag + dispatch~~   | ~~`cli.py`, `models.py`, `main.py`~~                                  | ❌ Out of scope — `--sync-schedule` to be removed |
| D4  | Config additions          | `.env.example`                                                        | ✅     |
| D5  | Mapping additions         | `data/schedule_mapping.json.example`                                  | ✅     |
| D6  | Dependency                | `requirements.txt`                                                    | ✅     |
| D7  | Tests                     | `tests/test_google_sheets_adapter.py` ✅ / ~~`tests/test_schedule_sync.py`~~ ❌ | Partial — sync tests to be deleted |

---

## Test results

```
126 passed in 0.88s
```

- 113 pre-existing tests: all green (zero regressions)
- 13 new tests: all green (7 adapter + 6 sync)

> ⚠️ 6 sync tests (`test_schedule_sync.py`) cover out-of-scope code and will be removed in refactor. Post-refactor count: 120 (113 pre-existing + 7 adapter).

---

## Files changed

### New files
- `google_sheets_adapter.py` — `get_staff_list(sheet_id, tab_name, credentials_path) → list[dict]`; `get_schedule_grid(sheet_id, tab_name, credentials_path) → list[list]`; uses `gspread.service_account` ✅
- ~~`schedule_sync.py`~~ — ❌ out of scope; to be deleted
- `tests/test_google_sheets_adapter.py` — 7 tests: name/dept dict mapping, empty name filtering, empty sheet, 2D grid passthrough, credentials path forwarding, sheet ID + tab name routing ✅
- ~~`tests/test_schedule_sync.py`~~ — ❌ out of scope; to be deleted

### Modified files
- `requirements.txt` — added `gspread==6.1.4` ✅
- ~~`cli.py`~~ — ❌ `--sync-schedule` flag to be removed; `args.sync_schedule` to be removed from `_admin_modes`; `sync_schedule` branch to be removed
- ~~`models.py`~~ — ❌ `sync_schedule` to be removed from `mode` docstring
- ~~`main.py`~~ — ❌ `sync_schedule` dispatch block to be removed
- `.env.example` — added `GOOGLE_SHEET_ID` and `GOOGLE_SERVICE_ACCOUNT_JSON` ✅
- `data/schedule_mapping.json.example` — added `"staff_tab": "Staff"` and `"schedule_tab": "Schedule"` ✅

---

## Architecture decisions implemented

| AD             | Decision                                                                                                                         |
|----------------|----------------------------------------------------------------------------------------------------------------------------------|
| AD-S006a-001   | `gspread.service_account(filename=credentials_path)` — service account auth, no user interaction ✅                             |
| AD-S006a-002   | `staff_tab` and `schedule_tab` read from `schedule_mapping.json` — IT-configurable ✅                                           |
| AD-S006a-003   | `get_staff_list` returns `list[{name, department}]`; `get_schedule_grid` returns raw 2D list ✅                                  |
| ~~AD-S006a-004~~ | ~~`schedule_sync.run_sync` writes XLSX~~                                                                                       | ❌ Out of scope — wrong assumption; to be removed |
| ~~AD-S006a-005~~ | ~~`--sync-schedule` flag~~                                                                                                     | ❌ Out of scope — wrong assumption; to be removed |
| AD-S006a-006   | `GOOGLE_SERVICE_ACCOUNT_JSON` is an absolute path; credentials never in git ✅                                                   |

---

## Prerequisites before UAT (one-time IT setup)

1. **Google Cloud project** — create project, enable Google Sheets API
2. **Service account** — create service account, download JSON key to `~/Shedule_bot/data/service_account.json`
3. **Share the Sheet** — share the Google Sheet with the service account email (Viewer permission)
4. **`.env`** — add:
   ```
   GOOGLE_SHEET_ID=<your-sheet-id>
   GOOGLE_SERVICE_ACCOUNT_JSON=/home/<username>/Shedule_bot/data/service_account.json
   ```
5. **`schedule_mapping.json`** — confirm `staff_tab` matches the actual tab name in the Sheet
6. **`pip install`** — `source venv/bin/activate && pip install gspread==6.1.4`

---

## UAT checklist (Owner)

> ⚠️ U006a-1 through U006a-5 referenced `--sync-schedule` which is out of scope. UAT checklist to be redefined after refactor.

- [ ] U006a-6: POC1 notification pipeline untouched — `--dry-run` output identical to pre-S006a behaviour
