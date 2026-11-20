#!/bin/bash
set -euo pipefail
J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24m
ulimit -v 15000000
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export PYTHONDONTWRITEBYTECODE=1 XDG_CACHE_HOME="$J/work/build24m4m/cache" TMPDIR="$J/work/build24m4m/tmp"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
exec nice -n 10 bwrap --ro-bind / / --bind "$J" "$J" --dev-bind /dev /dev --proc /proc --chdir "$J" /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$J/work/build24m4m/bootstrap.py" "$@"
