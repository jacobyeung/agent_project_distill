**36 tests and two fresh-process import checks passed** for the exact SHA256 below. [VALIDATION.json](/scratch/jjyeung/orch_n30/lever1_c/r1/out/VALIDATION.json) records `passed=true`, including rehearsal naming, capture, ordering, and telemetry checks.

The injected failure passed production fetch and receipt validation. The fetched `0.tgz` contained the decoded `metadata/7.json` traceback.

Forecast: **23.75 worker / 37.75 allocation minutes**. The increase adds six minutes for loading and one for staging/telemetry. **The ≤34-minute target remains unmet**: eliminating that entire staging allowance still leaves 36.75 minutes; further savings lack timing evidence.

Token: `a784b94c2e6af` — not placed.  
Delivery: **3,704,563 bytes**.  
SHA256:
```text
fba95b8b0b00c87ec7900817a0977084e18efed504b8918e24eccf9224302974
```

PLACE.md, REPORT.md, and BUILD.json agree. No fixtures moved.