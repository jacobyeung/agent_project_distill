#!/bin/bash
set -eu
cd "$(dirname "$0")/../.."
export TMPDIR="$PWD/work/tmp" CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME="$PWD/work/tmp/hf" XDG_CACHE_HOME="$PWD/work/tmp/cache" TORCH_HOME="$PWD/work/tmp/torch" TRITON_CACHE_DIR="$PWD/work/tmp/triton" CONDA_PKGS_DIRS="$PWD/work/tmp/conda"
ulimit -f 204800
exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
