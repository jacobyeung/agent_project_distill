#!/usr/bin/env bash
# CPU runner: nice 10, 8 threads, under 40 GB virtual memory, no CUDA device visible.
# Usage: bash kit/run_cpu.sh <p1cpu|sam3> <script.py> [args...]
set -euo pipefail
cd "$(dirname "$0")"
case "$1" in
  p1cpu) PY=/scratch/jjyeung/envs/p1cpu/bin/python ;;
  sam3) PY=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python ;;
  *) echo "unknown interpreter $1" >&2; exit 2 ;;
esac
shift
ROOT="$(cd .. && pwd)"
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME="$ROOT/work/cache" HF_HOME="$ROOT/work/hf" TRITON_CACHE_DIR="$ROOT/work/triton"
export MPLCONFIGDIR="$ROOT/work/mpl" TMPDIR="$ROOT/work/tmp" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
mkdir -p "$TMPDIR"
ulimit -v 40000000
exec nice -n 10 "$PY" -B "$@"
