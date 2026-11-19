#!/bin/bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_cafix/review
mkdir -p logs
for module in mc_guard mc_population mc_frames mc_step0 mc_seeds; do
  args=()
  case "$module" in mc_step0|mc_seeds) args=(all) ;; esac
  bash review_run.sh p1cpu review_run.py "$module" "${args[@]}" > "logs/$module.log" 2>&1
done
for stub in seed raster empty; do
  bash review_run.sh p1cpu review_run.py mc_stubs "$stub" > "logs/stub_$stub.log" 2>&1
done
for tag in S_A0_STUBSEED S_GT_STUBRASTER S_A0_STUBEMPTY; do
  bash review_run.sh p1cpu review_run.py mc_price "$PWD/out/v2/dry/track/$tag" "$PWD/out/v2/dry/price/$tag" > "logs/price_$tag.log" 2>&1
done
bash review_run.sh p1cpu review_run.py mc_summary dry > logs/summary.log 2>&1
