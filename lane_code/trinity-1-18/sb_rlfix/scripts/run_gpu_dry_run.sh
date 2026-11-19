#!/bin/bash
set -eu
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export XDG_CACHE_HOME="$PWD/out/cache" HF_HOME="$PWD/out/hf" TMPDIR="$PWD/out/tmp"
export WORLD_SIZE=1 RANK=0 LOCAL_RANK=0
export PYTHONPATH="$PWD/overlay${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p "$TMPDIR"
# The operator supplies an assigned GPU through CUDA_VISIBLE_DEVICES and a GPU environment.
exec nice -n 10 "${RL_PYTHON:-python}" -B scripts/dry_run.py "$@"
