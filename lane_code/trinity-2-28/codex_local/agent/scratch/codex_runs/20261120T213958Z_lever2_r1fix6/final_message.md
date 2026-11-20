- **Allocation: 50 minutes; worker cap: 30 minutes.** Forecast: **23.75 worker / 37.75 total minutes**, leaving **6.25 / 12.25 minutes** of headroom. The forecast does not justify a 35-minute cap.
- **Import audit:** 332 Python files scanned; zero unresolved reachable imports. Environment evidence and exclusions are recorded in [IMPORT_AUDIT.json](out/IMPORT_AUDIT.json).
- **Validation:** all **43 tests**, both fresh-process import checks, CPU rehearsal scans, capture doubles and production failure-fetch checks passed. [VALIDATION.json](out/VALIDATION.json) records `passed=true`.
- **Token:** `a784b94c2e6af` — not placed.
- **Delivery:** **3,704,924 bytes**. PLACE, REPORT and BUILD agree.

SHA256:
`87a55270aa3ed70b5e00021284a4284f8eb6ca1116c1cd35ee6fe810e6365041`