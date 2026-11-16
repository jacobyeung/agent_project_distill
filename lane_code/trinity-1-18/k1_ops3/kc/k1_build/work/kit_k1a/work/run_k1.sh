#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 8 ]]; then
  echo 'Usage: run_k1.sh NODE CARD MANIFEST OUTPUT VNICE GPU_PY PHASE SECONDS [--tower-cache DIR --own-cache DIR] [--cpu-fixture]' >&2
  exit 2
fi
node=$1
card=$2
manifest=$3
output=$4
vnice=$5
py=$6
phase=$7
seconds=$8
shift 8
[[ $(hostname -s) == "$node" && "$node" == trinity-*-* ]]
[[ "$card" =~ ^[0-7]$ && "$output" == /scratch/* && "$vnice" == /scratch/* && -x "$vnice" && -x "$py" ]]
[[ "$phase" == tower_sam || "$phase" == own || "$phase" == convert ]]
[[ "$seconds" =~ ^[1-9][0-9]*$ ]]
work=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export CUDA_VISIBLE_DEVICES="$card"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export XDG_CACHE_HOME="$output/runtime_cache" HF_HOME="$output/runtime_cache" TRITON_CACHE_DIR="$output/runtime_cache"
"$py" -I -s -B "$work/verify_sources.py"
exec "$vnice" "$py" -I -s -B "$work/watchdog.py" --out "$output" --stall 900 --seconds "$seconds" -- \
  "$py" -I -s -B "$work/k1_pipeline.py" cache --manifest "$manifest" --out "$output" --phase "$phase" --max-seconds "$seconds" --preflight-out "$output.preflight.json" "$@"
