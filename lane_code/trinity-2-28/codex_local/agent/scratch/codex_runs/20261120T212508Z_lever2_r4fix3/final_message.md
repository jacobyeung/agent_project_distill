Fixed `score.py` to allow `3.jsonl` and `4.json`. No other return consumer had the whitelist mismatch.

All **30 checks passed**: 24 existing tests, three real finalization → fetch → scorer cases (success, timeout after four pairs, worker failure), and three archive rejection checks. Evidence: [FIX3_CHECKS.json](/scratch/jjyeung/orch_n30/lever1_c/r4kit/out/FIX3_CHECKS.json).

FROZEN and delivery bytes remain unchanged.

- Token: `d93a17be024f5`
- Delivery: **4,235,885 bytes**
- SHA-256: `9d023abcd0335d57ce99f02e54961b20838c3114c9cd3b537056d4532ca2ef36`