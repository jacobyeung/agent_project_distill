Token proof passed: True.

Peak sampled card memory (MiB): 123.0.

| Arm | Identical token arrays | Mean actual score | Mean accepted score |
|---|---:|---:|---:|
| ON16k | 1/1 | 1.0 | 1.0 |
| B2048 | 1/1 | 1.0 | 1.0 |
| B4096 | 1/1 | 1.0 | 1.0 |

Per-item comparison (zero-based divergence; no numerical rounding):

| Arm | ID | Tokens equal | First divergence | Accepted length | Actual length | Raw equal | Answer equal | Score equal | Seconds | Tokens/s |
|---|---|---|---|---|---|---|---|---|---|---|
| ON16k | item | True | None | 3 | 3 | True | True | True | None | None |
| B2048 | item | True | None | 3 | 3 | True | True | True | None | None |
| B4096 | item | True | None | 3 | 3 | True | True | True | None | None |

llguidance audit: null
Failure reasons: []

Maximum observed 1 s nvidia-smi sample; shorter peaks may be missed.

Timing uses worker journals and budget receipts. Reused rows have no new budget latency. Missing values remain null. Concurrent request latency is not wall-clock throughput.
