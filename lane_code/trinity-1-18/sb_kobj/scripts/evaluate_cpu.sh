#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_kobj
export CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8
export PYTHONPATH="$PWD/code" XDG_CACHE_HOME="$PWD/work/cache" TMPDIR="$PWD/work" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
ulimit -v 39845888
CPU_PYTHON="${CPU_PYTHON:-/scratch/jjyeung/envs/planner_local_v1/bin/python}"
case "$CPU_PYTHON" in /scratch/*) ;; *) exit 2 ;; esac
exec "$CPU_PYTHON" code/evaluate.py "$@"
