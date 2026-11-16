Repeated token proof passed: False.

| Comparison | ON16k tokens | B2048 tokens | B4096 tokens | Passed |
|---|---|---|---|---|
| Run 1 vs accepted | 1/1 | 1/1 | 1/1 | True |
| Run 2 vs accepted | 0/1 | 0/1 | 0/1 | False |
| Run 1 vs run 2 | False | False | False | False |

| Arm | Answers equal between runs | Scores equal between runs |
|---|---|---|
| ON16k | False | False |
| B2048 | False | False |
| B4096 | False | False |

Per-item arrays and first divergence are in RUN_TO_RUN.json. Each run retains its full accepted comparison and sandbox receipt.
Failure reasons: []
