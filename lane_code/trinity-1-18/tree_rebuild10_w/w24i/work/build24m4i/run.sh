#!/bin/bash
set -euo pipefail
ulimit -v 16000000
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 STUDENT_IO_THREADS=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
ROOT=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24i
export TMPDIR="$ROOT/work/build24m4i/tmp"
exec nice -n 10 /usr/bin/bwrap --ro-bind / / --bind "$ROOT" "$ROOT" --dev /dev --proc /proc --chdir "$ROOT" /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
