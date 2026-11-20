#!/bin/bash
set -eu
cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24o3
ulimit -v 16000000
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/work/build24m4o3/tmp"
export XDG_CACHE_HOME="$PWD/work/build24m4o3/cache" HF_HOME="$PWD/work/build24m4o3/cache/hf" TRITON_CACHE_DIR="$PWD/work/build24m4o3/cache/triton"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
