#!/bin/bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_cachk
for arm in S_A0_STUBSEED S_GT_STUBRASTER S_A0_STUBEMPTY; do
 bash kit_v2/run_cpu.sh p1cpu ../work/patched_run.py mc_price "$PWD/work/review/out/v2/dry/track/$arm" "$PWD/work/patched/out/v2/dry/price/$arm" > "out/check/patched_price_$arm.log" 2>&1
done
bash kit_v2/run_cpu.sh p1cpu ../work/patched_run.py mc_summary dry > out/check/patched_summary.log 2>&1
bash kit_v2/run_cpu.sh sam3 mc_preflight.py > out/check/preflight_patched.log 2>&1
