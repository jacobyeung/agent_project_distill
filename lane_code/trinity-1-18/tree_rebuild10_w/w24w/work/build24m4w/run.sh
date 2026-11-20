#!/bin/bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24w
ulimit -v 14680064
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 STUDENT_IO_THREADS=1
export TMPDIR="$PWD/work/build24m4w/tmp" XDG_CACHE_HOME="$PWD/work/build24m4w/tmp" HF_HOME="$PWD/work/build24m4w/tmp" TORCH_HOME="$PWD/work/build24m4w/tmp" TRITON_CACHE_DIR="$PWD/work/build24m4w/tmp"
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
