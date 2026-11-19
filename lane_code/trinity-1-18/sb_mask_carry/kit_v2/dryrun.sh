#!/usr/bin/env bash
# The CPU dry run in order (logs in work/v2/logs). BARS_FROZEN.json is written first, before any priced number.
#   bash kit_v2/dryrun.sh
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$KIT")"
L="$ROOT/work/v2/logs"; mkdir -p "$L"
R="bash $KIT/run_cpu.sh"
O="$ROOT/out/v2"
$R p1cpu mc_bars.py > "$L/bars.log" 2>&1
$R p1cpu mc_guard.py > "$L/guard.log" 2>&1
$R p1cpu mc_frames.py > "$L/frames.log" 2>&1
$R p1cpu mc_step0.py all > "$L/step0.log" 2>&1
$R p1cpu mc_seeds.py 5 > "$L/seeds5.log" 2>&1
$R p1cpu mc_seeds.py all --phr-parity > "$L/seeds_all.log" 2>&1
$R p1cpu mc_stubs.py seed > "$L/stub_seed.log" 2>&1
$R p1cpu mc_stubs.py raster > "$L/stub_raster.log" 2>&1
$R p1cpu mc_price.py "$O/dry/track/S_A0_STUBSEED" "$O/dry/price/S_A0_STUBSEED" > "$L/price_stubseed.log" 2>&1
$R p1cpu mc_price.py "$O/dry/track/S_GT_STUBRASTER" "$O/dry/price/S_GT_STUBRASTER" > "$L/price_stubraster.log" 2>&1
$R p1cpu mc_summary.py dry > "$L/summary_dry.log" 2>&1
$R sam3 mc_probe_predictor.py > "$L/predictor.log" 2>&1 || true
$R sam3 mc_track_pass.py --device cpu --out "$O/dry/track_cpu" --captures arkitscenes/41048124 --max-frames 8 \
  --sets S_A0/D64,S_GT/D64,S_A0/A32,S_GT/A32 --project-after 1 > "$L/track_cpu.log" 2>&1
for s in S_A0_D64 S_GT_D64 S_A0_A32 S_GT_A32; do
  $R p1cpu mc_price.py "$O/dry/track_cpu/$s" "$O/dry/price_cpu/$s" arkitscenes/41048124 >> "$L/price_cpu.log" 2>&1
done
bash "$KIT/manifest.sh"
$R p1cpu mc_staging.py > "$L/staging.log" 2>&1
(cd "$ROOT" && CUDA_VISIBLE_DEVICES='' nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B -m pytest -q -p no:cacheprovider kit_v2/tests) > "$L/tests.log" 2>&1
$R p1cpu mc_dryrun_report.py > "$L/dryrun_report.log" 2>&1
