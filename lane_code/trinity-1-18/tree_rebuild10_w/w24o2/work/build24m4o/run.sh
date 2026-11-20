#!/bin/bash
set -eu
cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24o2
ulimit -v 16777216
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/work/build24m4o/tmp"
export XDG_CACHE_HOME="$PWD/work/build24m4o/cache" HF_HOME="$PWD/work/build24m4o/cache/hf" TRITON_CACHE_DIR="$PWD/work/build24m4o/cache/triton"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
