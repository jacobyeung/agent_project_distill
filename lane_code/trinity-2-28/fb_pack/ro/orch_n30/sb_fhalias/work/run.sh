#!/bin/bash
set -u
cd /scratch/jjyeung/orch_n30/sb_fhalias
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR="$PWD/work/tmp" XDG_CACHE_HOME="$PWD/work/cache" HF_HOME="$PWD/work/hf" TORCH_HOME="$PWD/work/torch"
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B "$@"
