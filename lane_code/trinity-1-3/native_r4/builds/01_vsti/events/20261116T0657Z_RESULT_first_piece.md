RESULT: The adapter, camera-only dispatcher and CPU item loop are implemented.

Comparator rescoring reproduces 450 scores per comparator and primaries 66.95 and 68.71 (`out/SCORER_CHECK.json`).
The CPU loop completes all 9 locally available items with replay equality (`work/j2/COMPLETE.json`).
The brief says 11 sample items; the supplied item file contains 9 for the supplied scenes (`work/a0/TASKS.jsonl`).
This CPU loop uses a synthetic raw tower and synthetic checkpoint prefill (`work/t1/RAW.json`, `work/g1/GEOMETRY.json`).
GPU decode, real tower inference, namespace execution, remote staging and historical equality are not checked.
