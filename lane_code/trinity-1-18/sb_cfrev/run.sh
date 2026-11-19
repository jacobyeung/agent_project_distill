#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_cfrev
export CUDA_VISIBLE_DEVICES=''
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export XDG_CACHE_HOME="$PWD/tmp/.cache" HF_HOME="$PWD/tmp/hf" TRITON_CACHE_DIR="$PWD/tmp/triton"
export MPLCONFIGDIR="$PWD/tmp/matplotlib" TMPDIR="$PWD/tmp"
mkdir -p "$TMPDIR"
ulimit -v 39000000
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B "$@"
