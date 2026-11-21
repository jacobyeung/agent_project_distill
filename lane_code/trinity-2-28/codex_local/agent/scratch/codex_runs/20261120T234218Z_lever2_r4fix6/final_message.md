Implemented in [src/monitor.py:39](/scratch/jjyeung/orch_n30/lever1_c/r4kit/src/monitor.py:39):

`max(0, memory.current − min(active_file + inactive_file, max(0, file − shmem)))`

This retains shmem without double-counting it. Missing counters fall back to process-tree RSS. Thresholds remain **180/110 GiB**; every return includes all four memory peaks.

**37 tests passed**, including synthetic cache/anon cases. Delivery and requested metadata rebuilt; `FROZEN.json` unchanged.

- Token: `eb331eb9af6a4`
- Delivery: `out/delivery.tgz`, **4,252,135 bytes**
- SHA-256: `66a28190724bb61b6ca373f75fc4d22c6955d96d0158459fcdfd05d4c1106419`