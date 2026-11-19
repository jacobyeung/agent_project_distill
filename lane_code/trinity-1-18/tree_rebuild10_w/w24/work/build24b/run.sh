#!/bin/bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/work/tmp" XDG_CACHE_HOME="$PWD/work/tmp/cache" HF_HOME="$PWD/work/tmp/hf" TORCH_HOME="$PWD/work/tmp/torch"
ulimit -v 20971520
ulimit -f 204800
date -u
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
