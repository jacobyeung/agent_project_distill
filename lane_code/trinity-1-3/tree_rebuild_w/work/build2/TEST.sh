#!/bin/bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/tree_rebuild
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/work/tmp"
ulimit -f 204800
exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build2/run_tests.py "$@"
