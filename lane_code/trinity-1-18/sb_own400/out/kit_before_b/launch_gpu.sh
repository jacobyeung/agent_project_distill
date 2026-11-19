#!/bin/bash
set -euo pipefail
ROOT=/scratch/jjyeung/orch_n30/sb_own400
cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
exec nice -n 10 /scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12 -B kit/launcher.py "$@"
