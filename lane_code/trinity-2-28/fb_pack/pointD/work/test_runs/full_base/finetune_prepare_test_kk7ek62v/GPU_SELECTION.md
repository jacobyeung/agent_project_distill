# Local GPU qualification

Status: diagnostic, provisional. Checked trinity-0-18 at 2026-11-19T21:15:38.438824+00:00.
No GPU has been allocated. Qualification does not replace a fresh check and an actual coordination lease at launch.

| GPU | Free MiB | Compute rows | Qualifies | Reason |
|---|---:|---:|---|---|
| 0 | 49040 | 1 | False | 1 compute process rows |
| 1 | 29140 | 0 | False | fewer than 40000 MiB free |
| 2 | 49135 | 0 | True | Zero compute rows and sufficient free memory |

Qualifying indices: `[2]`. Preferred OneThinker GPU: `2`.
OneThinker is blocked by trainer admission, not by this availability check. Qwen is skipped by the lane parameters.
