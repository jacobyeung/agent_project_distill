#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/fb_pack/point
export OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
export XDG_CACHE_HOME="$PWD/cache" HF_HOME="$PWD/cache/hf" TRITON_CACHE_DIR="$PWD/cache/triton"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B code/pointing_locate.py "$@"
