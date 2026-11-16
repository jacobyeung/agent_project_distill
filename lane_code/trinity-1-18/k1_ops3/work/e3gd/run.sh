#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/k1_ops3/work/e3gd
export CUDA_VISIBLE_DEVICES=''
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME="$PWD/out/.cache" HF_HOME="$PWD/out/.cache/hf" TRITON_CACHE_DIR="$PWD/out/.cache/triton"
export MPLCONFIGDIR="$PWD/out/.cache/matplotlib" TMPDIR="$PWD/out/tmp"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME" "$HF_HOME" "$TRITON_CACHE_DIR" "$MPLCONFIGDIR"
exec /scratch/jjyeung/envs/planner_local_v1/bin/python -B harness.py "$@"
