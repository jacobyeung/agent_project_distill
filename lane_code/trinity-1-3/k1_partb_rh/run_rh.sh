#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
P=runtime/uv/bin/python3.12
if [[ ! -x "$P" ]]; then
    P=/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12
fi
exec nice -n 19 "$P" -I -s -B rh_prepare.py
