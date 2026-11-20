#!/bin/bash
set -euo pipefail
ulimit -v 15000000
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 STUDENT_IO_THREADS=1
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
export TMPDIR="$ROOT/work/build24m4g/tmp"
exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
