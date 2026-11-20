All four fixes are implemented:

- Durable startup logs, ERR/EXIT traps, and streaming child diagnostics. First-line, extraction, missing-env, and oversized-publication failures pass [production fetch tests](/scratch/jjyeung/orch_n30/lever1_c/r1/out/BOOTSTRAP_CHECKS.json).
- Assigned-job storage requires ext4; tmpfs, xfs, and btrfs are rejected.
- `/project` budget: **48,000,000 bytes per job**, including placement. Guards and breakdown are in [PLACE.md](/scratch/jjyeung/orch_n30/lever1_c/r1/PLACE.md).
- CPU/GPU submissions share batch bytes, environment, and `--export=NONE`; only GRES differs. Real startup and environment-inventory checks pass.

[VALIDATION.json](/scratch/jjyeung/orch_n30/lever1_c/r1/out/VALIDATION.json): **passed=true**, 55 tests plus both import checks, bound to the exact delivery.

Token: `a6f198d3c7b20`  
Delivery: **3,719,932 bytes**  
SHA256: `bb5315a268af467e2015a590f9fbe383e604e22c9accb1f40cc5e0b81fb0f2a4`

Checksums verified. No placement or submission ran.