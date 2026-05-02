# Known Risks

## RISK-001 — worldtimeapi.org availability (clock drift monitor)

**Raised:** 2026-05-02  
**Sprint:** S004b  
**Component:** `_check_clock_drift()` in `main.py`  
**ISO 25010:** Reliability

**Description:**  
The clock drift monitor queries `worldtimeapi.org` — a free public API with no uptime SLA. If the API is unavailable for an extended period, every `--production` run logs a `WARNING: Clock drift check skipped`. Repeated warnings may cause IT to start ignoring the WARNING level in logs, reducing the effectiveness of all other warnings (alert fatigue).

**Likelihood:** Low (API is generally stable)  
**Impact:** Medium (degrades observability of real clock drift)

**Current mitigation:**  
- Failure is non-blocking — send loop is not affected
- README documents that repeated "skipped" warnings during an API outage are expected, not clock drift

**Proposed future mitigation (not in scope S004b):**  
Add a secondary fallback time API (e.g., `timeapi.io`) tried when `worldtimeapi.org` is unreachable.
