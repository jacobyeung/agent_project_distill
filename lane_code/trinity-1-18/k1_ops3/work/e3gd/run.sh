#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/k1_ops3/work/e3gd
export CUDA_VISIBLE_DEVICES=''
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME="$PWD/.cache" HF_HOME="$PWD/.cache/hf" TRITON_CACHE_DIR="$PWD/.cache/triton"
export MPLCONFIGDIR="$PWD/.cache/matplotlib" TMPDIR="$PWD/tmp"
mkdir -p "$TMPDIR" out
exec /scratch/jjyeung/envs/planner_local_v1/bin/python -B harness.py "$@"
