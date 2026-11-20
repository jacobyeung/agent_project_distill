#!/bin/bash
set -euo pipefail
ulimit -v 15000000
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/setup24m4m.py
