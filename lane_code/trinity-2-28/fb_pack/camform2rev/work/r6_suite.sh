#!/bin/bash
# Usage: r6_suite.sh TREE OUTDIR ; runs each affected test module with a timeout, verbose, into OUTDIR/TREE/<module>.log
# Test-output env vars point at a per-tree fixtures dir (same set the build's code/suite.py used).
cd "$(dirname "$0")"
T=$1; O=$PWD/${2:-suite}/$T; F=$PWD/tmp/fx_$T; mkdir -p $O $F
export CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 TMPDIR=$F HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
for k in B2_TEST_OUTPUT B9_TEST_OUTPUT B11_TEST_OUTPUT R2_PROOFS R2_FIXTURES STUDENT_PILOT_TEST_OUTPUT STUDENT_CONVERTER_TEST_OUTPUT LANE_TEST_OUTPUT CLEAN_VSI590K_TEST_ROOT; do export $k=$F/fixtures; done
MODS="test_merge11 test_r1_build13 test_r1_build14 test_r1_build15 test_r1_build16 test_r1_build17 test_r1_build18 test_r1_build19 test_r1_build20 test_r1_export17 test_r2_build12 test_r2_build_n1 test_r2_n1fix test_r2_n1fix2 test_r2_n1fix3"
cd tree_$T
for m in $MODS; do
  timeout 1500 nice -n 10 env OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
    /scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest tests.$m -v > $O/$m.log 2>&1
  echo "$m rc=$?" >> $O/rc.txt
done
echo DONE >> $O/rc.txt
