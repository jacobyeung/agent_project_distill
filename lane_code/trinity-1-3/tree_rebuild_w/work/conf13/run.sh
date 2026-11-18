#!/bin/bash
set -eu
cd /scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf13/pkg
export TMPDIR="$PWD/work/tmp" CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8
ulimit -f 204800
exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$@"
