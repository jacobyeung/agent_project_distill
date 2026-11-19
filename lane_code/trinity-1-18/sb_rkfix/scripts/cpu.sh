#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export OPENBLAS_NUM_THREADS=8 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 NUMEXPR_NUM_THREADS=1
export TMPDIR="$PWD/tmp" XDG_CACHE_HOME="$PWD/cache" HF_HOME="$PWD/cache/hf" TORCH_HOME="$PWD/cache/torch"
export PYTHONPATH="$PWD/scripts"
exec nice -n 10 /scratch/jjyeung/envs/planner_local_v1/bin/python -B "$@"
