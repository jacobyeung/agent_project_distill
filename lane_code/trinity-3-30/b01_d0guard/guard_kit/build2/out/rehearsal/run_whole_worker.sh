#!/bin/bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build2
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export XDG_CACHE_HOME="$PWD/work/cache" HF_HOME="$PWD/work/cache/hf" TRITON_CACHE_DIR="$PWD/work/cache/triton"
unset PYTHONPATH
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/rehearsal/run_whole_worker.py "$@"
