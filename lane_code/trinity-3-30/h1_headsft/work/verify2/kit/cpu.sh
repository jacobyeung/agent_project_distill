#!/bin/bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/h1_headsft/work/verify2/kit
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 MKL_NUM_THREADS=16 NUMEXPR_NUM_THREADS=16
export PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR="$PWD/tmp" XDG_CACHE_HOME="$PWD/tmp/cache" HF_HOME="$PWD/tmp/hf" TRITON_CACHE_DIR="$PWD/tmp/triton"
export PYTHONPATH="$PWD/tree:$PWD${PYTHONPATH:+:$PYTHONPATH}"
export LANE_TEST_OUTPUT="$PWD/tmp"
ulimit -v 33554432
exec /scratch/jjyeung/envs/p1cpu/bin/python -B "$@"
