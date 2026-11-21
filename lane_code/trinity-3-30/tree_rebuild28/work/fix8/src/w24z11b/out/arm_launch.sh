#!/bin/bash
set -euo pipefail
umask 077
ulimit -v 14680064
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
HERE="${BASH_SOURCE[0]%/*}"
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$HERE/arm_launch.py" "$@"
