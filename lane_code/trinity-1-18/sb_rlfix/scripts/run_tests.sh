#!/bin/bash
set -eu
cd "$(dirname "$0")/.."
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export PYTHONPATH="$PWD/overlay:$PWD/tests"
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B scripts/check.py
