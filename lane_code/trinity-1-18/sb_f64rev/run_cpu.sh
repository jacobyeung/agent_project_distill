#!/bin/bash
set -eu
cd /scratch/jjyeung/orch_n30/sb_f64rev
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR="$PWD/tmp" HF_HOME="$PWD/tmp/hf" XDG_CACHE_HOME="$PWD/tmp/cache"
export TORCH_HOME="$PWD/tmp/torch" TRITON_CACHE_DIR="$PWD/tmp/triton" MALLOC_ARENA_MAX=4
export PYTHONPATH=/scratch/jjyeung/orch_n30/sb_f64/work/pyext_tv
mkdir -p "$TMPDIR"
ulimit -v 39062500
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -s -B "$@"
