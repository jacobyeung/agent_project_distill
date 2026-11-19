#!/bin/bash
set -u
G=/scratch/jjyeung/orch_n30/so_git/work; O=$G/review_round4_source; W=$G/realgit5_by_swarm_opt
[[ -f $O/tests/run_real_git_owner.sh ]] || { echo "no source"; exit 2; }
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
mkdir -p $W/py36 $W/py312
for k in py36 py312; do py=/usr/bin/python3; [[ $k == py312 ]] && py=/scratch/jjyeung/envs/p1cpu/bin/python
  (cd $O && LCS_RUN_REAL_GIT_TESTS=1 LCS_REVIEW2_FIXES=1 LCS_REAL_GIT_WORK=$W/$k LCS_PYTHON=$py nice -n 10 timeout 900 bash tests/run_real_git_owner.sh > $W/run_$k.txt 2>&1; echo "rc=$?" >> $W/run_$k.txt)
done
echo REALGIT_DONE > $W/DONE
