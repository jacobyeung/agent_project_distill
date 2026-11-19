#!/bin/bash
set -eu
ulimit -v 19000000
ulimit -f 204800
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export TMPDIR=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tmp
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
