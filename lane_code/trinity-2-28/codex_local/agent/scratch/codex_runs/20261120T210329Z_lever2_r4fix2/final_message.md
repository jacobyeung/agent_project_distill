Fixed and rebuilt. All **24 tests pass**.

- CPU/GPU fetch passes **22 injected failure cases**.
- Authenticated returns include packed tracebacks bounded to 200 lines. Real worker failures fetch and decode locally; deny-list scans pass.
- Returned batch timings govern admission. The slow-batch test retains four complete pairs and rejects the next batch.

FROZEN.json is unchanged. PLACE.md, REPORT.md, BUILD.json and FORECAST.json agree. Forecast: **1,367.2 s**, still based on unmeasured GPU throughput.

Token: `d93a17be024f5`  
Delivery: [out/delivery.tgz](/scratch/jjyeung/orch_n30/lever1_c/r4kit/out/delivery.tgz) — **4,235,885 bytes**  
SHA-256: `9d023abcd0335d57ce99f02e54961b20838c3114c9cd3b537056d4532ca2ef36`