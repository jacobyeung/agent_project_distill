#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_kbox
export CUDA_VISIBLE_DEVICES=''
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME="$PWD/.cache" HF_HOME="$PWD/.cache/hf" TRITON_CACHE_DIR="$PWD/.cache/triton"
export MPLCONFIGDIR="$PWD/.cache/matplotlib" TMPDIR="$PWD/tmp"
mkdir -p "$TMPDIR"
ulimit -v 40000000
exec /scratch/jjyeung/envs/planner_local_v1/bin/python -B "$@"
