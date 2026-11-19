#!/bin/bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_cachk/work/review
bash review_run.sh p1cpu review_run.py mc_population > logs/population.log 2>&1
bash review_run.sh p1cpu review_run.py mc_stubs empty > logs/stub_empty.log 2>&1
bash review_run.sh p1cpu review_run.py mc_price "$PWD/out/v2/dry/track/S_A0_STUBEMPTY" "$PWD/out/v2/dry/price/S_A0_STUBEMPTY" > logs/price_empty.log 2>&1
bash review_run.sh p1cpu review_run.py mc_summary dry > logs/summary_complete.log 2>&1
