#!/bin/bash
set -euo pipefail
export PYTHONPATH=tools PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
exec prlimit --as=21474836480 /scratch/jjyeung/envs/p1cpu/bin/python -B "$@"
