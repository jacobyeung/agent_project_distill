#!/bin/bash
set -euo pipefail
L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24
cd "$L"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR="$L/work/tmp" XDG_CACHE_HOME="$L/work/tmp/cache" HF_HOME="$L/work/tmp/hf" TORCH_HOME="$L/work/tmp/torch"
export TK_JOB_START="$(date +%s)"
ulimit -v 19000000
ulimit -f 204800
status=0
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build24f/rehearsal_runner.py || status=$?
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build24f/check_rehearsal.py || status=1
exit "$status"
