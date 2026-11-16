Token proof passed: False.

Peak sampled card memory (MiB): None.

| Arm | Identical token arrays | Mean actual score | Mean accepted score |
|---|---:|---:|---:|
| ON16k | 0/1 | None | 1.0 |
| B2048 | 0/1 | None | 1.0 |
| B4096 | 0/1 | None | 1.0 |

Per-item comparison (zero-based divergence; no numerical rounding):

| Arm | ID | Tokens equal | First divergence | Accepted length | Actual length | Raw equal | Answer equal | Score equal | Seconds | Tokens/s |
|---|---|---|---|---|---|---|---|---|---|---|
| ON16k | item | False | None | 3 | None | False | False | False | None | None |
| B2048 | item | False | None | 3 | None | False | False | False | None | None |
| B4096 | item | False | None | 3 | None | False | False | False | None | None |

llguidance audit: null
Failure reasons: ["ON16k results: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)"]

Maximum observed 1 s nvidia-smi sample; shorter peaks may be missed.

Timing uses worker journals and budget receipts. Reused rows have no new budget latency. Missing values remain null. Concurrent request latency is not wall-clock throughput.
