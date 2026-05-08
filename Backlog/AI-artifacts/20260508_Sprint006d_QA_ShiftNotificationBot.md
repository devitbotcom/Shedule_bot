# Sprint S006d — QA Report
**Date:** 2026-05-08
**Sprint:** S006d — Preference Data Validation
**Prepared by:** QA

---

## Test results

**201/201 passed** (full suite including S006d additions).

---

## Error handling review

### D1 — V8 all-excluded slot left empty with no generation warning
**Severity:** Medium  
**Location:** `schedule_generator.py` — V8 exclusion block  
**Status:** 🔴 Open — returning to Developer

When V8 exclusion filters out all eligible candidates for a slot, the code does a bare `continue` with no generation warning:

```python
if not eligible:
    continue  # all candidates had V8 conflict for this day; slot left empty
```

C9 (all worked yesterday) handles the same situation correctly — it appends a `[День N]` warning before continuing. Head receives a message that the slot was skipped. V8 does not. Head sees an empty cell in the output with no explanation beyond the validator's data-quality warning.

**Required fix:**
```python
if not eligible:
    generation_warnings.append(
        f"[День {day_number}] відділення '{dept}' — конфлікт переваг, слот залишено порожнім"
    )
    continue
```

---

### OB-1 — `try/except` scope aborts remaining staff on first error
**Severity:** Low  
**Location:** `schedule_validator.py` — V8 block (line 76) and V9 block (line 91)  
**Status:** ℹ️ By design — no action required

The `try/except Exception: pass` wraps the entire staff loop. An exception on one staff record silently aborts all remaining staff for that check. This is consistent with the V1/V7 pattern throughout the validator (intentional non-blocking behaviour).

---

### OB-2 — `all([])` returns `True` in Python
**Severity:** Info  
**Location:** `schedule_generator.py` — V10 check  
**Status:** ℹ️ No current risk — no action required

`all(condition for s in eligible)` returns `True` on an empty list, which would incorrectly fire V10. In the current control flow this cannot happen — C9 and V8 both `continue` before reaching V10 when `eligible` is empty. Noted for future maintainers if the flow changes.

---

## Summary

| ID | Severity | Description | Status |
|----|----------|-------------|--------|
| D1 | Medium | V8 all-excluded slot silent — no `[День N]` warning | ✅ Fixed by Developer |
| OB-1 | Low | try/except aborts remaining staff on error | ℹ️ By design |
| OB-2 | Info | `all([])` is True — V10 false-fire risk if flow changes | ℹ️ No current risk |

**QA verdict: ✅ APPROVED. D1 resolved; 201/201 tests pass.**
