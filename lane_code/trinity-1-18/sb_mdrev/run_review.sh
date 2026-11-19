#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_mdrev
export CUDA_VISIBLE_DEVICES=''
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1
ulimit -v 39000000
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B audit.py "${1:-all}"
