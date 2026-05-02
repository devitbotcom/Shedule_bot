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

---

## RISK-002 — `other` shift midnight-crossing not explained to IT

**Raised:** 2026-05-02  
**Sprint:** S004b  
**Component:** README P8 / cPanel cron entry for `--shift-type other`  
**ISO 25010:** Operability

**Description:**  
The `other` shift fires at 01:25 Kyiv time = 22:25 UTC the previous calendar day. The cPanel cron entry fires at `25 22 * * *` — a day before the shift date in UTC terms. The `TZ=Europe/Kyiv` prefix ensures the bot correctly identifies the next-day Kyiv date, but this is not explained in the README. IT seeing a cron fire at 22:25 for a shift dated the following day may suspect a misconfiguration and "fix" the cron entry, breaking the behaviour.

**Likelihood:** Medium (Owner already encountered confusion about this during S004 testing)  
**Impact:** Medium (IT changes cron time, `other` shifts stop firing on correct date)

**Current mitigation:**  
- `TZ=Europe/Kyiv` prefix is present in the documented cron entry — behaviour is correct
- ARCH AD-S004b-001 documents the midnight-crossing logic

**Proposed future mitigation:**  
Add one explanatory sentence to README P8 next to the `other` cron entry clarifying that 22:25 UTC = 01:25 Kyiv next day, and that `TZ=` prefix handles the date correctly.
