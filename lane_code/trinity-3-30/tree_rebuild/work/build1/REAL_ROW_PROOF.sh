#!/bin/bash
set -eu
cd /scratch/jjyeung/orch_n30/tree_rebuild
export TMPDIR="$PWD/work/tmp" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 STUDENT_R2_LOCAL_NODE=1
ulimit -f 204800
if [ "$#" -eq 1 ]; then
    exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build4/rows_proof.py "$1"
fi
if [ "$#" -ne 2 ]; then
    printf 'Usage: REAL_ROW_PROOF.sh <rows_dir> <sealed_meta_dir>\n' >&2
    exit 2
fi
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build1/real_proof_entry.py "$1" "$2" --output "$PWD/work/tmp/real_row_proof"
