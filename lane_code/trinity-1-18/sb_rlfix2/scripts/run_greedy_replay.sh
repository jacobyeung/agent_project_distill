#!/bin/bash
set -eu
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export XDG_CACHE_HOME="$PWD/out/cache" HF_HOME="$PWD/out/hf" TORCH_HOME="$PWD/out/torch"
export TRITON_CACHE_DIR="$PWD/out/triton" TORCHINDUCTOR_CACHE_DIR="$PWD/out/inductor" TMPDIR="$PWD/out/tmp"
mkdir -p "$TMPDIR"
export PYTHONPATH="$PWD/overlay${PYTHONPATH:+:$PYTHONPATH}"
exec nice -n 10 "${RL_PYTHON:?Set RL_PYTHON to the assigned GPU environment interpreter}" -B scripts/greedy_replay.py "$@"
