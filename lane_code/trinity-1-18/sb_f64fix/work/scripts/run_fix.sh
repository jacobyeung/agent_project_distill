#!/bin/bash
# CPU wrapper for sb_f64fix: nice 10, 8 threads, 40 GB address-space cap, offline, every write under this workspace.
# Reads the trainer tree, Qwen meta files, fixtures and reader package from sb_f64 (read-only).
set -eu
W=/scratch/jjyeung/orch_n30/sb_f64fix
S=/scratch/jjyeung/orch_n30/sb_f64
mkdir -p "$W/work/tmp" "$W/work/dryrun"
export TMPDIR="$W/work/tmp" CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MALLOC_ARENA_MAX=4
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME="$W/work/tmp/hf" XDG_CACHE_HOME="$W/work/tmp/cache"
export TORCH_HOME="$W/work/tmp/torch" TRITON_CACHE_DIR="$W/work/tmp/triton"
export F64_TREE="$S/pkg/work/tree_f64" F64_WORK="$W/work/dryrun" F64_META="$S/in/qwen35_9b_meta"
export F64_CONFIG="${F64_CONFIG:-$W/kit/configs/r1_config_f64.json}" F64_READER_ROOT="${F64_READER_ROOT:-$W/work/reader_root}"
export STUDENT_FRAME_ROOT_MAP='{}' STUDENT_ORCHARD=1
# torchvision 0.26.0+cpu unpacked by sb_f64 (Qwen3VLVideoProcessor needs it), then the trainer tree.
export PYTHONPATH="$S/work/pyext_tv:$F64_TREE"
ulimit -v 39062500
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -s -B "$@"
