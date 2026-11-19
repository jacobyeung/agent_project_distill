#!/bin/bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/tree_rebuild
export TMPDIR="$PWD/work/tmp" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
ulimit -f 204800
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build3/card.py
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build3/report_host.py
