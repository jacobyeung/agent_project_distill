#!/bin/bash
set -eu
L=/scratch/jjyeung/orch_n30/tree_rebuild_w
export TMPDIR="$L/work/tmp" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export HF_HOME="$TMPDIR/hf" XDG_CACHE_HOME="$TMPDIR/cache" TORCH_HOME="$TMPDIR/torch" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export R2_FAST_CENSUS=1
ulimit -f 204800
cd "$L"
exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
