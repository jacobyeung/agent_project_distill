#!/bin/bash
set -euo pipefail
K=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
: "${PY:=python}"
output=
threads=16
args=("$@")
for ((i=0; i<${#args[@]}; i++)); do
  case "${args[i]}" in
    --output) output=${args[i+1]:-} ;;
    --output=*) output=${args[i]#*=} ;;
    --threads) threads=${args[i+1]:-} ;;
    --threads=*) threads=${args[i]#*=} ;;
  esac
done
if [[ -z "$output" || ! "$threads" =~ ^([1-9]|[1-5][0-9]|6[0-4])$ ]]; then
  echo 'Require --output DIR and --threads in 1..64' >&2
  exit 2
fi
output=$(realpath -m -- "$output")
case "$output" in
  /home|/home/*|/data*|/lustre|/lustre/*)
    echo '--output must be node-local' >&2; exit 2 ;;
esac
mkdir -p -- "$output/tmp"
output=$(cd -- "$output" && pwd)
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=17
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="$threads" MKL_NUM_THREADS="$threads" OPENBLAS_NUM_THREADS="$threads" NUMEXPR_NUM_THREADS="$threads"
export TMPDIR="$output/tmp" XDG_CACHE_HOME="$output/tmp/cache" HF_HOME="$output/tmp/hf" TRITON_CACHE_DIR="$output/tmp/triton"
export PYTHONPATH="${PY_OVERLAY:+$PY_OVERLAY:}$K/tree:$K"
cd -- "$K"
# Deliberately no address-space cap: the real CPU model needs 60–120+ GB.
exec "$PY" -B "$K/first_batch/real_fixture_batch.py" "${args[@]}" --output "$output"
