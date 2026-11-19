#!/bin/bash
set -euo pipefail
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME=/scratch/jjyeung/orch_n30/so_read/work/cache
export HF_HOME=/scratch/jjyeung/orch_n30/so_read/work/cache/hf
export TRITON_CACHE_DIR=/scratch/jjyeung/orch_n30/so_read/work/cache/triton
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
