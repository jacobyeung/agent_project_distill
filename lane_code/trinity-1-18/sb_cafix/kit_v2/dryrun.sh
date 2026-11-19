#!/usr/bin/env bash
# The CPU dry run in order (logs in work/v2/logs). BARS_FROZEN.json (written once, before any priced number) is verified,
# and BARS_AMENDMENT.json is registered after POPULATION.json and before any pricing.
#   bash kit_v2/dryrun.sh            (MC_DRYRUN_FULL=0 skips the 40-minute full-capture tracker run of step 4)
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$KIT")"
L="$ROOT/work/v2/logs"; mkdir -p "$L" "$ROOT/work/v2/tmp"
R="bash $KIT/run_cpu.sh"
O="$ROOT/out/v2"
FULL_CAPTURE=arkitscenes/41048124
$R p1cpu mc_guard.py > "$L/guard.log" 2>&1
$R p1cpu mc_population.py > "$L/population.log" 2>&1
$R p1cpu mc_bars.py > "$L/bars.log" 2>&1
$R p1cpu mc_frames.py > "$L/frames.log" 2>&1
$R p1cpu mc_step0.py all > "$L/step0.log" 2>&1
$R p1cpu mc_seeds.py 5 > "$L/seeds5.log" 2>&1
$R p1cpu mc_seeds.py all --phr-parity > "$L/seeds_all.log" 2>&1
for k in seed raster empty; do
  $R p1cpu mc_stubs.py "$k" > "$L/stub_$k.log" 2>&1
done
for s in S_A0_STUBSEED S_GT_STUBRASTER S_A0_STUBEMPTY; do
  $R p1cpu mc_price.py "$O/dry/track/$s" "$O/dry/price/$s" > "$L/price_$s.log" 2>&1
done
$R p1cpu mc_summary.py dry > "$L/summary_dry.log" 2>&1
$R sam3 mc_probe_predictor.py > "$L/predictor.log" 2>&1 || true
if [ "${MC_DRYRUN_FULL:-1}" = 1 ]; then
  $R sam3 mc_track_pass.py --device cpu --out "$O/dry/track_cpu_full" --captures "$FULL_CAPTURE" --hard-stop 2700 \
    --project-after 1 > "$L/track_cpu_full.log" 2>&1 || true
fi
: > "$L/price_cpu_full.log"
for d in "$O"/dry/track_cpu_full/S_*; do
  if [ -d "$d" ]; then
    $R p1cpu mc_price.py "$d" "$O/dry/price_cpu_full/$(basename "$d")" "$FULL_CAPTURE" >> "$L/price_cpu_full.log" 2>&1
  fi
done
bash "$KIT/manifest.sh"
$R p1cpu mc_staging.py > "$L/staging.log" 2>&1
(cd "$ROOT" && CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 \
  /scratch/jjyeung/envs/p1cpu/bin/python -B -m pytest -q -p no:cacheprovider --basetemp "$ROOT/work/v2/tmp/pytest" kit_v2/tests) \
  > "$L/tests.log" 2>&1 || true
$R p1cpu mc_dryrun_report.py > "$L/dryrun_report.log" 2>&1
