#!/bin/bash
set -eu
L=/scratch/jjyeung/orch_n30/tree_rebuild_w
export TMPDIR="$L/work/tmp" OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export HF_HOME="$TMPDIR/hf" XDG_CACHE_HOME="$TMPDIR/cache" TORCH_HOME="$TMPDIR/torch" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 R2_FAST_CENSUS=1
ulimit -f 204800
cd "$L"
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$L/work/lane_stop/stop_multirank.py"
