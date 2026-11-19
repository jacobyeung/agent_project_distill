#!/bin/bash
set -eu
J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l
ulimit -v 19922944
ulimit -f 204800
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 STUDENT_IO_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR="$J/work/tmp" XDG_CACHE_HOME="$J/work/tmp/cache" HF_HOME="$J/work/tmp/hf"
export TORCH_HOME="$J/work/tmp/torch" TRITON_CACHE_DIR="$J/work/tmp/triton"
export LANE_TEST_OUTPUT="$J/work/tmp" R2_LANE_ROOT="$J/work/validation/lane" R2_PROOFS="$J/work/validation/proofs"
exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
