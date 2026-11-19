#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_kobj
: "${GPU:?Set one authorized GPU index}"
: "${PYTHON:?Set a local /scratch Python with staged torch and dependencies}"
: "${GO_FILE:?Set the pinned authorization/registration JSON under /scratch}"
case "$PYTHON" in /scratch/*) ;; *) exit 2 ;; esac
export CUDA_VISIBLE_DEVICES="$GPU" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8
export PYTHONPATH="$PWD/code" XDG_CACHE_HOME="$PWD/work/cache" HF_HOME="$PWD/work/hf" TRITON_CACHE_DIR="$PWD/work/triton" TMPDIR="$PWD/work"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
ulimit -v 39845888
# Both steps debit this arm's same cumulative budget. A killed reservation blocks resume.
remaining=$(CUDA_VISIBLE_DEVICES= /scratch/jjyeung/envs/planner_local_v1/bin/python code/budget.py s1_sam)
(( remaining > 0 && remaining <= 7200 ))
exec flock -n "$PWD/work/gpu.lock" /data3/shared/scripts/vnice/vnice.sh timeout --signal=KILL "${remaining}s" "$PYTHON" code/gpu_pass.py s1_sam --go "$GO_FILE" --cut-level "${CUT_LEVEL:-0}"
