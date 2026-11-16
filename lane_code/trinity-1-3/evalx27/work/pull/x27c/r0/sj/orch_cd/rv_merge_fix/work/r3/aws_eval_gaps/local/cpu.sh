#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 XDG_CACHE_HOME="$PWD/checks/cache" HF_HOME="$PWD/checks/cache/hf"
export PYTHONPATH=/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages:/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages
exec /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B "$@"
