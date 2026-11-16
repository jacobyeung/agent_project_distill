#!/bin/bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/k1_ops3/work/partb/build
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/evidence/build6b_tmp" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
P=/scratch/jjyeung/envs/p1cpu/bin/python
trap 'rc=$?; printf "%s\n" "$rc" > evidence/REPORT6B_DRIVER_EXIT.txt' EXIT
nice -n 19 "$P" -B check_report6.py > evidence/REPORT6B_REGRESSIONS.log 2>&1
nice -n 19 "$P" -B rh_batch.py --diagnostic-python "$P" > evidence/REPORT6B_BATCH.log 2>&1
nice -n 19 "$P" -B build_rh.py --pack-env > evidence/REPORT6B_PACK.log 2>&1
