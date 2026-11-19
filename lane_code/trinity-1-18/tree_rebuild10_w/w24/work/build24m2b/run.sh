#!/bin/bash
set -euo pipefail
ulimit -v 19000000
ulimit -f 204800
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 STUDENT_IO_THREADS=1
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tmp
exec /scratch/jjyeung/envs/p1cpu/bin/python -s -B "$@"
