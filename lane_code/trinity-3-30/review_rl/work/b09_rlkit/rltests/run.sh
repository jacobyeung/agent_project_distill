#!/bin/bash
# CPU only. Usage: bash rltests/run.sh [module ...]
cd /scratch/jjyeung/orch_n30/review_rl/work/b09_rlkit
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
export TMPDIR=/scratch/jjyeung/orch_n30/review_rl/work/b09_rlkit/work/tmp; mkdir -p $TMPDIR
ulimit -f 4194304
exec /scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest ${@:-discover -s rltests -t .} -v
