#!/bin/bash
cd /scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12; export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/tmp; ulimit -f 204800
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B s/mut.py "$@" > mut_$1.log 2>&1; echo "DONE rc=$? $(date -u +%T)" >> mut_$1.log
