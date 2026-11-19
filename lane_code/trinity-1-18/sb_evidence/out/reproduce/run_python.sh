#!/bin/bash
set -eu
cd /scratch/jjyeung/orch_n30/sb_evidence
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
export TMPDIR="$PWD/work/tmp" R2_PROOFS="$PWD/work/proofs" R2_FIXTURES=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/fixtures
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME="$PWD/work/cache/hf" XDG_CACHE_HOME="$PWD/work/cache" TORCH_HOME="$PWD/work/cache/torch"
ulimit -v 39845888
exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
