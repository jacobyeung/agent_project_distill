#!/bin/bash
set -eu
cd /scratch/jjyeung/orch_n30/fb_pack/pointD
export OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export XDG_CACHE_HOME="$PWD/work/cache" HF_HOME="$PWD/work/hf" TORCH_HOME="$PWD/work/torch"
export TMPDIR="$PWD/work/tmp"
mkdir -p "$TMPDIR"
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B "code/$1.py" "${@:2}"
