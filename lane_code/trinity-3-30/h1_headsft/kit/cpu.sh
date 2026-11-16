#!/bin/bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 MKL_NUM_THREADS=16 NUMEXPR_NUM_THREADS=16
export PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR="$PWD/tmp/b4" XDG_CACHE_HOME="$PWD/tmp/b4/cache" HF_HOME="$PWD/tmp/b4/hf" TRITON_CACHE_DIR="$PWD/tmp/b4/triton"
mkdir -p "$TMPDIR"
export PYTHONPATH="$PWD/tree:$PWD${PYTHONPATH:+:$PYTHONPATH}"
export LANE_TEST_OUTPUT="$PWD/tmp/b4"
ulimit -v 33554432
exec /scratch/jjyeung/envs/p1cpu/bin/python -B "$@"
