# QA Test Suite Delivery Report

**Date:** 2026-05-03
**Role:** QA
**Scope:** Full test suite review — 92 tests across 10 files
**Suite status:** 92/92 passing

---

## Legend

### Design techniques

| Term                              | Meaning                                                                                                                                                                                                                   |
|-----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **EP** — Equivalence Partitioning | Input space is divided into partitions where all values behave the same way. One representative value per partition is tested. Example: testing one valid token and one missing token, rather than every possible string. |
| **BVA** — Boundary Value Analysis | Tests focus on the edges of valid/invalid ranges, where bugs most commonly occur. Example: threshold at 300 s → test at 299 s and 301 s.                                                                                  |
| **State-based**                   | Test verifies the system state before and after an operation (e.g. record written to DB, file created). Outcome is checked by inspecting stored state, not just return value.                                             |
| **Negative**                      | Test provides invalid or forbidden input and verifies the system rejects it correctly (e.g. exits with correct code, raises expected exception).                                                                          |
| **Error path**                    | Test simulates a failure in a dependency (network, subprocess, file) and verifies the system handles it gracefully — correct log level, correct exit code, no unhandled exception.                                        |
| **Contract**                      | Test verifies a non-functional guarantee: non-blocking behaviour, no mutation of input, no exception propagated. The *what* is less important than the *how*.                                                             |
| **Regression**                    | Test written specifically to prevent a known past bug from reappearing. Named after the bug it guards (e.g. BUG-001).                                                                                                     |
| **Snapshot / Golden master**      | Test compares full output against a pre-approved reference string. Catches any structural change to the output, even if individual field tests still pass.                                                                |
| **Idempotency**                   | Test verifies that running the same operation twice produces the same result as running it once — no corruption, duplication, or error on repeat.                                                                         |
| **Combinatorial**                 | Test exercises a specific combination of two or more flags/options that interact. Not all combinations are tested — only those with non-obvious interaction.                                                              |
| **Precondition**                  | Test verifies that the system reads a specific config value from the mapping rather than using a hardcoded fallback. Done by setting the value to something wrong and confirming the system fails in the expected way.    |

### Redundant / inefficient column

| Symbol           | Meaning                                                                                                                         |
|------------------|---------------------------------------------------------------------------------------------------------------------------------|
| ✅                | Clean — no overlap, no waste                                                                                                    |
| ⚠️ Mergeable     | Two tests share identical setup; the second adds only one extra assert. Can be combined into one test with no loss of coverage. |
| ⚠️ Overlaps with | The test re-asserts something already covered by another test. May still be kept for readability or as a canary.                |

---

## Coverage by file

| File                        | Tests | Notes                                                    |
|-----------------------------|-------|----------------------------------------------------------|
| `test_cli.py`               | 15    | CLI argument parsing and mutual-exclusion guards         |
| `test_clock_drift.py`       | 4     | Clock drift monitor (AD-S004b-008)                       |
| `test_config.py`            | 3     | Environment variable loading                             |
| `test_db.py`                | 9     | SQLite DB init, dedup read/write, clear, WAL             |
| `test_format_message.py`    | 11    | Telegram message rendering                               |
| `test_gen_crontab.py`       | 16    | Crontab install, idempotency, fallback, self-removal     |
| `test_health_extensions.py` | 5     | `[SCHEDULE]` / `[ENV TIME]` / `[TZ OFFSET]` health lines |
| `test_schedule_parser.py`   | 15    | XLSX parsing, mapping config, mtime guard                |
| `test_shift_logic.py`       | 6     | Prev/next colleague chain computation                    |
| `test_telegram_adapter.py`  | 8     | HTTP send, error wrapping, token security, health check  |

---

## test_cli.py (15)

| Test                                       | Main purpose                         | Design technique           | Redundant / inefficient |
|--------------------------------------------|--------------------------------------|----------------------------|-------------------------|
| `test_no_flags_is_health`                  | Default mode + all defaults          | EP — empty input partition | ✅                       |
| `test_production`                          | `--production` sets mode             | EP                         | ✅                       |
| `test_dry_run`                             | `--dry-run` sets mode AND flag       | EP                         | ✅                       |
| `test_production_employee`                 | `--employee` passes name through     | EP                         | ✅                       |
| `test_production_force`                    | `--force` sets flag                  | EP                         | ✅                       |
| `test_reload_schedule`                     | `--reload-schedule` mode             | EP                         | ✅                       |
| `test_reload_schedule_dry_run`             | Two-flag combination                 | Combinatorial              | ✅                       |
| `test_force_without_production_exits`      | Guard: `--force` alone rejected      | Negative                   | ✅                       |
| `test_employee_without_production_exits`   | Guard: `--employee` alone rejected   | Negative                   | ✅                       |
| `test_dry_run_with_production_exits`       | Mutual exclusion                     | Negative                   | ✅                       |
| `test_production_date`                     | `--date` passes value                | EP                         | ✅                       |
| `test_date_without_production_exits`       | Guard: `--date` alone rejected       | Negative                   | ✅                       |
| `test_date_invalid_format_exits`           | Format validation at parse time      | BVA — invalid format       | ✅                       |
| `test_shift_type`                          | `--shift-type` passes value          | EP                         | ✅                       |
| `test_shift_type_without_production_exits` | Guard: `--shift-type` alone rejected | Negative                   | ✅                       |

---

## test_clock_drift.py (4)

| Test                                                    | Main purpose                   | Design technique | Redundant / inefficient                                            |
|---------------------------------------------------------|--------------------------------|------------------|--------------------------------------------------------------------|
| `test_clock_drift_ok_logs_info`                         | Delta within threshold → INFO  | State-based      | ✅                                                                  |
| `test_clock_drift_warning_when_delta_exceeds_threshold` | Delta > 300 s → WARNING        | BVA — threshold  | ✅                                                                  |
| `test_clock_drift_warning_when_api_unreachable`         | API exception → WARNING logged | Error path       | ⚠️ Same setup as `_does_not_raise` — mergeable                     |
| `test_clock_drift_does_not_raise_on_api_failure`        | Non-blocking contract          | Contract         | ⚠️ Subset of above — single additional assert, not a separate case |

---

## test_config.py (3)

| Test                         | Main purpose                          | Design technique     | Redundant / inefficient |
|------------------------------|---------------------------------------|----------------------|-------------------------|
| `test_all_vars_present`      | Happy path — all vars load            | EP — valid partition | ✅                       |
| `test_missing_one_var`       | Single missing var → exit 1 with name | Negative / EP        | ✅                       |
| `test_missing_multiple_vars` | Multiple missing → all names reported | Negative / EP        | ✅                       |

---

## test_db.py (9)

| Test                                        | Main purpose                  | Design technique       | Redundant / inefficient |
|---------------------------------------------|-------------------------------|------------------------|-------------------------|
| `test_db_created`                           | File created on first run     | State-based            | ✅                       |
| `test_schema_idempotent`                    | Double `init_db` safe         | Idempotency            | ✅                       |
| `test_wal_mode`                             | WAL pragma active             | State-based            | ✅                       |
| `test_was_notified_false_when_empty`        | Empty DB → pending            | Boundary — empty state | ✅                       |
| `test_was_notified_true_after_ok_record`    | `ok` record → dedup fires     | State-based            | ✅                       |
| `test_was_notified_false_after_fail_record` | `fail` record → still pending | State-based            | ✅                       |
| `test_clear_only_specified_dates`           | Date scope isolation          | State-based            | ✅                       |
| `test_get_pending_count`                    | Mixed state → correct count   | State-based            | ✅                       |
| `test_last_run_summary_empty`               | Empty DB → safe zero values   | Boundary — empty state | ✅                       |

---

## test_format_message.py (11)

| Test                                                | Main purpose                       | Design technique      | Redundant / inefficient                                                                                |
|-----------------------------------------------------|------------------------------------|-----------------------|--------------------------------------------------------------------------------------------------------|
| `test_message_contains_employee_name`               | Name present in output             | EP                    | ✅                                                                                                      |
| `test_date_displayed_as_dd_mm_yyyy`                 | ISO → DD-MM-YYYY conversion        | EP — format           | ✅                                                                                                      |
| `test_prev_name_shown_when_present`                 | Prev colleague name rendered       | EP                    | ✅                                                                                                      |
| `test_prev_shown_as_dash_when_missing`              | Null prev → dash, line not omitted | Boundary — null       | ✅                                                                                                      |
| `test_no_double_period_for_name_ending_with_period` | BUG-001 regression                 | Regression            | ✅                                                                                                      |
| `test_next_line_shown_as_dash_when_missing`         | Null next → dash                   | Boundary — null       | ✅                                                                                                      |
| `test_next_time_is_1700_for_labor`                  | `labor` maps to 17:00              | EP — day type         | ✅                                                                                                      |
| `test_next_time_is_0900_for_holiday`                | `holiday` maps to 09:00            | EP — day type         | ⚠️ Both holiday and other assert `"09:00"` against same fixed HOURS dict — observable output identical |
| `test_next_time_is_0900_for_other`                  | `other` maps to 09:00              | EP — day type         | ⚠️ See above                                                                                           |
| `test_custom_shift_hours_used`                      | Custom hours override applied      | EP — config variation | ✅                                                                                                      |
| `test_full_message_structure`                       | Exact string golden master         | Snapshot              | ⚠️ Overlaps most assertions above — valuable as structural canary, not as new coverage                 |

---

## test_gen_crontab.py (16)

| Test                                                          | Main purpose                                  | Design technique     | Redundant / inefficient |
|---------------------------------------------------------------|-----------------------------------------------|----------------------|-------------------------|
| `test_labor_kyiv_to_server`                                   | 17:00 Kyiv → 10:00 EDT                        | EP — pure function   | ✅                       |
| `test_holiday_kyiv_to_server`                                 | 09:00 Kyiv → 02:00 EDT                        | EP — pure function   | ✅                       |
| `test_other_crosses_midnight`                                 | 01:25 Kyiv → 18:25 EDT prev day               | BVA — midnight wrap  | ✅                       |
| `test_same_timezone_no_offset`                                | Zero offset → no change                       | BVA — zero           | ✅                       |
| `test_gen_crontab_contains_all_shift_types`                   | All shift types in installed crontab          | EP                   | ✅                       |
| `test_gen_crontab_contains_verify_entry`                      | Verify entry present                          | EP                   | ✅                       |
| `test_gen_crontab_install_path_from_xlsx`                     | Path derived from XLSX_PATH                   | EP — path derivation | ✅                       |
| `test_gen_crontab_offset_failure_uses_placeholder`            | All subprocess fail → placeholders in stdout  | Error path           | ✅                       |
| `test_gen_crontab_contains_log_retention`                     | Log retention entry present                   | EP                   | ✅                       |
| `test_gen_crontab_installs_via_crontab`                       | `# shedule_bot` marker written                | Contract — install   | ✅                       |
| `test_gen_crontab_idempotent`                                 | Old bot entries replaced; unrelated line kept | Idempotency          | ✅                       |
| `test_gen_crontab_fallback_prints_entries_when_install_fails` | Crontab unavailable → stdout fallback         | Error path           | ✅                       |
| `test_gen_crontab_custom_shift_type_included`                 | Custom shift type in output                   | EP — QA-010          | ✅                       |
| `test_verify_cron_sends_to_group`                             | Message sent to correct chat_id               | EP                   | ✅                       |
| `test_verify_cron_exits_1_on_send_failure`                    | Send failure → exit 1                         | Negative             | ✅                       |
| `test_verify_cron_self_removes_entry`                         | Verify line removed; production lines kept    | State-based          | ✅                       |

---

## test_health_extensions.py (5)

| Test                                                     | Main purpose                           | Design technique | Redundant / inefficient                                            |
|----------------------------------------------------------|----------------------------------------|------------------|--------------------------------------------------------------------|
| `test_schedule_line_shows_shift_hours`                   | `[SCHEDULE]` renders all three values  | EP               | ✅                                                                  |
| `test_schedule_line_shows_error_when_mapping_unreadable` | `_shift_hours` raises → `[SCHEDULE] ❌` | Error path       | ✅                                                                  |
| `test_env_time_and_offset_shown`                         | `[ENV TIME]` and `[TZ OFFSET]` present | EP               | ✅                                                                  |
| `test_env_time_shows_error_when_subprocess_fails`        | Subprocess fails → `[ENV TIME] ❌`      | Error path       | ⚠️ Same setup as `_does_not_raise` — mergeable                     |
| `test_env_time_error_does_not_raise`                     | Failure is non-blocking                | Contract         | ⚠️ Subset of above — single additional assert, not a separate case |

---

## test_schedule_parser.py (15)

| Test                                                  | Main purpose                       | Design technique        | Redundant / inefficient |
|-------------------------------------------------------|------------------------------------|-------------------------|-------------------------|
| `test_valid_xlsx_returns_five_shifts`                 | Correct row count from fixture     | EP — happy path         | ✅                       |
| `test_date_stored_as_iso`                             | DD-MM-YYYY XLSX → ISO string       | EP — format             | ✅                       |
| `test_day_type_values_valid`                          | Only known day_type values emitted | EP                      | ✅                       |
| `test_department_field_populated`                     | Column header used as dept name    | EP                      | ✅                       |
| `test_employee_names_from_xlsx`                       | No row silently dropped            | EP                      | ✅                       |
| `test_all_shifts_use_group_chat_id`                   | chat_id propagated to every shift  | EP                      | ✅                       |
| `test_mtime_guard_raises_on_fresh_file`               | File < 60 s old → abort            | BVA — freshness         | ✅                       |
| `test_mtime_guard_passes_on_stale_file`               | File > 60 s old → proceeds         | BVA — freshness         | ✅                       |
| `test_missing_required_header_exits`                  | Renamed column → exit 1 with name  | Negative                | ✅                       |
| `test_urgencia_column_not_parsed`                     | Skip column never becomes a dept   | Negative — exclusion    | ✅                       |
| `test_missing_mapping_file_exits`                     | Missing JSON → exit 1              | Negative                | ✅                       |
| `test_mapping_with_custom_department_list`            | Custom dept list limits output     | EP — config variation   | ✅                       |
| `test_precondition_header_row_read_from_mapping`      | Wrong header_row → exit 1          | Precondition / negative | ✅                       |
| `test_precondition_date_column_read_from_mapping`     | Wrong date_column → exit 1         | Precondition / negative | ✅                       |
| `test_precondition_day_type_column_read_from_mapping` | Wrong day_type_column → exit 1     | Precondition / negative | ✅                       |

---

## test_shift_logic.py (6)

| Test                                  | Main purpose                        | Design technique | Redundant / inefficient |
|---------------------------------------|-------------------------------------|------------------|-------------------------|
| `test_middle_shift_has_prev_and_next` | Both neighbours found               | EP               | ✅                       |
| `test_first_shift_has_no_prev`        | First in chain → prev is None       | Boundary         | ✅                       |
| `test_last_shift_has_no_next`         | Last in chain → next is None        | Boundary         | ✅                       |
| `test_department_isolation`           | Dept A start ignores Dept B history | EP — isolation   | ✅                       |
| `test_pure_function_no_mutation`      | Input list not modified             | Contract         | ✅                       |
| `test_output_length_matches_input`    | No shifts dropped                   | Contract         | ✅                       |

---

## test_telegram_adapter.py (8)

| Test                                               | Main purpose                                       | Design technique        | Redundant / inefficient                                                                                                 |
|----------------------------------------------------|----------------------------------------------------|-------------------------|-------------------------------------------------------------------------------------------------------------------------|
| `test_send_success`                                | Happy path — no exception, correct URL and payload | EP                      | ✅                                                                                                                       |
| `test_send_raises_on_http_error`                   | HTTP 4xx wrapped in RuntimeError                   | Error path              | ✅                                                                                                                       |
| `test_send_raises_on_connection_error`             | Network error wrapped; token scrubbed              | Error path + security   | ✅                                                                                                                       |
| `test_send_token_not_in_exception`                 | Token never in exception string                    | Security / regression   | ⚠️ Token-absent assertion already covered in `test_send_raises_on_connection_error` — only error message string differs |
| `test_send_raises_on_telegram_api_error`           | HTTP 200 + `ok:false` raises                       | EP — Telegram API error | ✅                                                                                                                       |
| `test_health_check_returns_true_when_ok`           | Valid token → True                                 | EP                      | ✅                                                                                                                       |
| `test_health_check_returns_false_on_network_error` | Network error → False, no raise                    | Error path + contract   | ✅                                                                                                                       |
| `test_health_check_returns_false_on_bad_token`     | Invalid token → False                              | Negative                | ✅                                                                                                                       |

---

## Actionable findings

| #  | Severity | Finding                                                                                           | Tests affected                                                                                     |
|----|----------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| F1 | 🔵       | Mergeable — same setup split across two tests; second test adds one assert                        | `test_clock_drift_warning_when_api_unreachable` + `test_clock_drift_does_not_raise_on_api_failure` |
| F2 | 🔵       | Mergeable — same setup split across two tests; second test adds one assert                        | `test_env_time_shows_error_when_subprocess_fails` + `test_env_time_error_does_not_raise`           |
| F3 | 🔵       | Redundant security assertion — token-absent check duplicated across two identical error scenarios | `test_send_token_not_in_exception` fully covered by `test_send_raises_on_connection_error`         |
| F4 | 🔵       | Same observable output — both assert `"09:00"` against same fixed HOURS dict                      | `test_next_time_is_0900_for_holiday` + `test_next_time_is_0900_for_other`                          |
| F5 | 🔵       | Golden master overlaps — snapshot re-asserts what 8 earlier tests already verify individually     | `test_full_message_structure`                                                                      |

**Note:** F5 is low-risk overlap — the snapshot test retains value as a structural canary for template changes and is recommended to keep.

Merging F1 + F2 + removing F3 + F4 would reduce the suite from 92 to 88 tests with no loss of coverage.


## Quality Characteristics — POC-1

*Updated 2026-05-01 with primitives discovered during S003–S004.*

| Characteristic         | Sub-characteristic       | Requirement                                                                                        | Discovered / Raised       | Status         |
|------------------------|--------------------------|----------------------------------------------------------------------------------------------------|---------------------------|----------------|
| Functional suitability | Correctness              | All staff receive correct Telegram message. Verified by Owner UAT.                                 | S001                      | ✅ S003         |
| Functional suitability | Completeness             | prev/next colleague resolved across date boundaries — full month context required.                  | BUG-005 (S003)            | ✅ S003         |
| Reliability            | Fault tolerance          | Graceful error on all known failure modes. Exit 0/1. No silent skips.                              | S001                      | ✅ S003         |
| Reliability            | Recoverability           | Log written on every run including failures. SQLite audit trail per send attempt.                  | S001                      | ✅ S003         |
| Reliability            | Schedule correctness     | Cron fires at the time the Maintainer expects — `TZ` must match Maintainer's local timezone.       | NFR-S004-001 (S004 UAT)   | ✅ S004b — `TZ=` prefix in every cron entry; `time.tzset()` fix in `config.py`; `--gen-crontab` calculates server-local times automatically |
| Performance efficiency | —                        | Not measured — small staff volume, no SLA required.                                                | —                         | NA             |
| Usability              | Operability              | Health check, dry-run, production CLI modes produce human-readable output.                         | S001                      | ✅ S003         |
| Usability              | Configurability          | IT edits only `data/schedule_mapping.json` for shift timing — no crontab syntax knowledge needed.  | 004-2 (S004 UAT)          | ✅ S004         |
| Security               | Confidentiality          | No secrets in code or logs. `.env` not in Git. No PII in log output. Token never in exceptions.   | S001 + BUG-S004-001       | ✅ S004         |
| Compatibility          | Interoperability         | Standard XLSX (openpyxl), Telegram REST API. Adapter pattern isolates messenger dependency.        | S001                      | ✅ S003         |
| Maintainability        | Modifiability            | IT updates `.env` (group chat ID, timezone) without touching code.                                 | S001 + S004               | ✅ S004b — `--gen-crontab` reinstalls cron on any `shift_hours` change; DEPLOY.md P9b covers procedure |
| Maintainability        | Testability              | Unit tests cover all logic layers. No network calls in tests. Subprocess tests for scripts.        | S001 + QA S004            | ✅ S004         |
| Maintainability        | Analysability            | SQLite audit log. Timestamped log file on every run. CLI health check per component.              | S001                      | ✅ S003         |
| Maintainability        | Single source of truth   | `shift_hours` in `schedule_mapping.json` drives both message content and cron schedule.            | 004-2 (S004 UAT)          | ✅ S004         |
| Portability            | Installability           | `docker compose up -d cron` is the only command IT needs for local dev. Production: `--gen-crontab` installs all cron entries automatically — no cPanel UI interaction. | S004 + S004b              | ✅ S004b        |
| Portability            | Adaptability             | Messenger adapter pattern supports adding Viber (S007) without changes to orchestrator or parser.  | S001 + S004 ext           | ⏸ S007         |

---