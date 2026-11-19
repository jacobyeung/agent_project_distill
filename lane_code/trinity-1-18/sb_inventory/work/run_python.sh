#!/bin/bash
set -eu
cd /scratch/jjyeung/orch_n30/sb_inventory
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
export TMPDIR="$PWD/work/tmp" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export HF_HOME="$PWD/work/cache/hf" XDG_CACHE_HOME="$PWD/work/cache" TORCH_HOME="$PWD/work/cache/torch"
ulimit -v 39845888
exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
