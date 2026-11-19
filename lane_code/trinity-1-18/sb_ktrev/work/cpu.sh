#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_ktrev
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME="$PWD/work/cache" HF_HOME="$PWD/work/cache/hf" TRITON_CACHE_DIR="$PWD/work/cache/triton" MPLCONFIGDIR="$PWD/work/cache/mpl" TMPDIR="$PWD/work/tmp"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
ulimit -v 40000000
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B "$@"
