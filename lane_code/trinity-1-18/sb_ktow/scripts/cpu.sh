#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_ktow
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4
export XDG_CACHE_HOME="$PWD/runtime/cache" HF_HOME="$PWD/runtime/hf" TRITON_CACHE_DIR="$PWD/runtime/triton" MPLCONFIGDIR="$PWD/runtime/mpl" TMPDIR="$PWD/runtime/tmp"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
mkdir -p "$TMPDIR"
# Bound virtual address space and CPU thread pools for every kit process.
ulimit -v 40000000
exec /scratch/jjyeung/envs/sam3_scipy_ovl/bin/python -B "$@"
