#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_kobj3
export CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export PYTHONPATH="$PWD/code" XDG_CACHE_HOME="$PWD/work/cache" HF_HOME="$PWD/work/hf" TMPDIR="$PWD/work"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
ulimit -v 38000000
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python "$@"
