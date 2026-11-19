# Room kit S1k2

Run from /scratch/jjyeung/orch_n30/sb_rkfam. This copy is BLOCKED and authorizes no inference.

The registered K1 training inputs provide no independent room-area annotation or segmented floor mesh. All 110 captures are excluded. BLOCKER.md names the missing source and the paths checked; out/S1K2_GT_AUDIT.json lists every exclusion and input hash.

out/S1K2_RULE.md preregisters four footprint families, constant grids, room folds, metric and tie-break. No family score, bootstrap interval, winner or deployment constants exist. configs/KERNEL_PROVENANCE_S1K2.json has status MISSING and authorized_by pending orchestrator; it is not an approval-ready selection record. Do not approve the inherited kernel as an S1k2 result.

The original KERNEL_PROVENANCE.json and KERNEL_FROZEN.json remain unchanged. The kit has not been rebound. Old selection, test and dry-run receipts describe only the inherited kit; they do not validate S1k2. Supply authenticated GT room areas or floor meshes on local disk before running selection, rebinding and full validation.

Reproduce this blocked delivery with these commands, sequentially:

```bash
bash scripts/cpu.sh scripts/s1k2_audit.py > out/S1K2_AUDIT.log 2>&1
bash scripts/cpu.sh scripts/s1k2_delivery.py
bash scripts/cpu.sh scripts/s1k2_validate.py > out/S1K2_VALIDATE.log 2>&1
bash scripts/cpu.sh scripts/s1k2_delivery.py
bash scripts/cpu.sh scripts/s1k2_package.py > tmp/S1K2_PACKAGE.log 2>&1
```

The validation runs selected existing synthetic tests and checks that missing provenance blocks launch. The full original suite and dry run require prohibited evaluation inputs and are not run. No new-kernel inference validation is possible without a selected kernel.

All stages use CPU only, nice priority 10 and at most eight threads. No network, SSH, Git, GPU, process termination or external writes are permitted. Keep K1 held-out, R0-dev, dev-S1 and official items closed. The archive is out/sb_rkfam.tar; its checksum is out/sb_rkfam.tar.sha256. The S1k2 packager excludes inherited archives and prohibited evaluation payloads.
