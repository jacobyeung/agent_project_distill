#!/bin/bash
set -euo pipefail
export TMPDIR=/scratch/jjyeung/orch_n30/tree_rebuild_w/w12/work/tmp
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export XDG_CACHE_HOME="$TMPDIR/cache" HF_HOME="$TMPDIR/hf" TRITON_CACHE_DIR="$TMPDIR/triton"
ulimit -f 204800
cd /scratch/jjyeung/orch_n30/tree_rebuild_w/w12
exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
