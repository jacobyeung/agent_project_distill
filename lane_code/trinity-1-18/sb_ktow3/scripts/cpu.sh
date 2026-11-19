#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_ktow3
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME="$PWD/runtime/cache" HF_HOME="$PWD/runtime/hf" TRITON_CACHE_DIR="$PWD/runtime/triton" MPLCONFIGDIR="$PWD/runtime/mpl" TMPDIR="$PWD/runtime/tmp"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
mkdir -p "$TMPDIR"
# Bound virtual address space and CPU thread pools for every kit process.
ulimit -v 40000000
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B "$@"
