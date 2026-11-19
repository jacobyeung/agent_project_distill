#!/bin/bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/tree_rebuild
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/work/tmp" XDG_CACHE_HOME="$PWD/work/tmp/cache" HF_HOME="$PWD/work/tmp/hf" HF_HUB_OFFLINE=1
ulimit -f 204800
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build2/merge_all.py
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build2/classify.py
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build2/seal.py
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build2/report.py
