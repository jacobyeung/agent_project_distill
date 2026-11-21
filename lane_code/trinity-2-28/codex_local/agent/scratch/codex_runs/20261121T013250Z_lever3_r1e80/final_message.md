Fixed and validated.

- **Cause:** `q/vnice.sh:29` launches a watcher that retains stdout/stderr while sleeping at `q/terminator.sh:64`. The old capture reader blocked on EOF and raised E80 despite child exit 0.
- **Fix:** bounded nonblocking drain and proper join. Failure receipts now include child/worker exit codes or signals, the failed module, and the bounded `27.json` tail.
- **Tests:** all **76 passed**, including real pinned archives and all **411 modules through production capture**, using local bwrap and a safe 30-second watcher substitute. `VALIDATION.json` is true; handoffs, scripts, and checksums agree.
- **Token:** `a38bd627f901e`, superseding `a7e29d4c8f103`.
- **Delivery:** `out/delivery.tgz`, **3,720,424 bytes**.

SHA256: `ce3184950aa87588fe9e79aa4b93f3a9b4497127177676144917cfc2cea31f84`