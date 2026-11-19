#!/bin/bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_own400
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
exec nice -n 10 /scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12 -B kit/cpu_check_228.py "$@"
