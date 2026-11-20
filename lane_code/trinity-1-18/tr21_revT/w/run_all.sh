#!/bin/bash
# usage: run_all.sh <tree-name> <list>
cd /scratch/jjyeung/orch_n30/tr21_revT/w
T=$1; R=res3/$T; mkdir -p $R logs3/$T
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1
export R2_FIXTURES=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/fixtures R2_LANE_ROOT=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21
while read f; do
  export R2_PROOFS=/scratch/jjyeung/orch_n30/tr21_revT/w/tmp3/$T/proofs_${f%.py} LANE_TEST_OUTPUT=/scratch/jjyeung/orch_n30/tr21_revT/w/tmp3/$T/lane_${f%.py}; mkdir -p $R2_PROOFS $LANE_TEST_OUTPUT
  timeout 1500 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B runner.py $T $f $R/$f.json tmp3/$T/${f%.py} > logs3/$T/$f.log 2>&1
  echo "$f rc=$?" >> $R/_rc.txt
done < $2
echo DONE >> $R/_rc.txt
