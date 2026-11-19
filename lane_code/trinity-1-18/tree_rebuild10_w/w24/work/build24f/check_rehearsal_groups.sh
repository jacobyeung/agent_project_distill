#!/bin/bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24
ulimit -v 19000000
ulimit -f 204800
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR="$PWD/work/build24f/rehearsal3/tmp"
export XDG_CACHE_HOME="$TMPDIR/cache" HF_HOME="$TMPDIR/hf" TORCH_HOME="$TMPDIR/torch"
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build24f/check_rehearsal_groups.py
