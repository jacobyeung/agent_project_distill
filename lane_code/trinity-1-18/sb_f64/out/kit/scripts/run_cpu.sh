#!/bin/bash
# CPU wrapper for the dry run: 16 cores, 40 GiB address-space cap, offline, caches on local scratch.
set -eu
W=/scratch/jjyeung/orch_n30/sb_f64
mkdir -p "$W/work/tmp"
export TMPDIR="$W/work/tmp" CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16
export MALLOC_ARENA_MAX=4 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME="$W/work/tmp/hf" XDG_CACHE_HOME="$W/work/tmp/cache"
export TORCH_HOME="$W/work/tmp/torch" TRITON_CACHE_DIR="$W/work/tmp/triton"
ulimit -v 41943040
# p1cpu (local) plus the torchvision 0.26.0+cpu wheel unpacked under work/pyext_tv: Qwen3VLVideoProcessor needs torchvision.
export PYTHONPATH="$W/work/pyext_tv"
exec taskset -c 24-39 /scratch/jjyeung/envs/p1cpu/bin/python -s -B "$@"
