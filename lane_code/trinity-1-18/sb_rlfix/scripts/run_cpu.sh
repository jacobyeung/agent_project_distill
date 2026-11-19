#!/bin/bash
set -eu
cd "$(dirname "$0")/.."
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export XDG_CACHE_HOME="$PWD/out/cache" HF_HOME="$PWD/out/hf" TMPDIR="$PWD/out/tmp"
mkdir -p "$TMPDIR"
export PYTHONPATH="$PWD/overlay${PYTHONPATH:+:$PYTHONPATH}"
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B -m rl_on_n.cpu_proof "$@"
