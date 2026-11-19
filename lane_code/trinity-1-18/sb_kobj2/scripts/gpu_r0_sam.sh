#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_kobj2
: "${GPU:?Set one authorized GPU index}"
: "${PYTHON:?Set the staged GPU interpreter under /scratch}"
: "${GO_FILE:?Set authorization receipt under /scratch}"
case "$PYTHON" in /scratch/*) ;; *) exit 2 ;; esac
case "$GO_FILE" in /scratch/*) ;; *) exit 2 ;; esac
export CUDA_VISIBLE_DEVICES="$GPU" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export PYTHONPATH="$PWD/code" XDG_CACHE_HOME="$PWD/work/cache" HF_HOME="$PWD/work/hf" TRITON_CACHE_DIR="$PWD/work/triton" TMPDIR="$PWD/work"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
ulimit -v 39845888
# The lock covers admission and execution. No concurrent launches share this budget.
exec 9>"$PWD/work/gpu.lock"
flock -n 9
remaining=$(CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/budget.py r0_sam)
(( remaining > 0 && remaining <= 12600 ))
exec /data3/shared/scripts/vnice/vnice.sh timeout --signal=TERM --kill-after=5s "$((remaining-5))s" nice -n 10 "$PYTHON" code/gpu_pass.py r0_sam --go "$GO_FILE" --cut-level "${CUT_LEVEL:-0}"
