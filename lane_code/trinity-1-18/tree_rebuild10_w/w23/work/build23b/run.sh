#!/bin/bash
set -eu
cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w23
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8 STUDENT_IO_THREADS=1 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/work/tmp" XDG_CACHE_HOME="$PWD/work/tmp/cache" HF_HOME="$PWD/work/tmp/hf" TRITON_CACHE_DIR="$PWD/work/tmp/triton"
ulimit -v 20971520
ulimit -f 204800
date -u
exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
