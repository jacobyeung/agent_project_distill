#!/bin/bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/tree_rebuild
export TMPDIR="$PWD/work/tmp" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 R2_ALL_TESTS="${R2_ALL_TESTS:-1}"
ulimit -f 204800
exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build4/package.py
