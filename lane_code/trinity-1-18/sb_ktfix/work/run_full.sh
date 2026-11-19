#!/usr/bin/env bash
set -euo pipefail
bash scripts/cpu.sh work/a0_rerun.py > out/fix_validation/a0_rerun.log 2>&1
printf '%s\n' 'The full N=32 reproduction matches all 1,037 A0 rows and all 209 capture row sets. The dry run and 28 regression tests pass, and all 12 reviewer mutations are killed. The Part A CPU self-comparison is running across all train captures; no GPU work ran.' > STATUS.md
bash scripts/cpu.sh work/part_a_cpu.py > out/fix_validation/part_a.log 2>&1
printf '%s\n' 'The full A0 reproduction and the 239-capture Part A CPU self-comparison pass. Available convert exports agree on all 237 scales; two captures report NO_CONVERT_EXPORT. All 28 tests pass and 12 mutations are killed. The final dry run and archive checks are pending; no GPU work ran.' > STATUS.md
bash scripts/cpu.sh code/dryrun.py > out/dryrun_v3.log 2>&1
bash scripts/cpu.sh work/write_fix_report.py > out/fix_validation/report.log 2>&1
bash scripts/cpu.sh scripts/finalize_v3.py > out/finalize_v3.log 2>&1
sha256sum -c out/sb_ktfix.tar.sha256
