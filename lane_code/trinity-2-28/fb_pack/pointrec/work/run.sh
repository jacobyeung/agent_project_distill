#!/bin/bash
set -eu
cd /scratch/jjyeung/orch_n30/fb_pack/pointrec
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export XDG_CACHE_HOME="$PWD/work/cache" HF_HOME="$PWD/work/hf" TMPDIR="$PWD/work/tmp"
mkdir -p "$TMPDIR"
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B "work/$1.py" "${@:2}"
