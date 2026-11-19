#!/bin/bash
# Run once after the user approves the full local suite's heavy I/O.
set -euo pipefail
cd /scratch/jjyeung/orch_n30/r1_pkt
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export XDG_CACHE_HOME="$PWD/work/fix11_cache" HF_HOME="$PWD/work/fix11_cache/hf"
export TRITON_CACHE_DIR="$PWD/work/fix11_cache/triton" CONDA_PKGS_DIRS="$PWD/work/fix11_cache/conda"
PY=/scratch/jjyeung/envs/p1cpu/bin/python
"$PY" -B tools/run_local_checks.py > out/logs/fix11_local_checks.log 2>&1
"$PY" -B tools/report_fix11.py
