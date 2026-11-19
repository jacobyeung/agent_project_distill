#!/bin/bash
set -u
G=/scratch/jjyeung/orch_n30/so_git/work; O=$G/review_round3_source
echo "owner dir: $O"; [[ -f $O/tests/run_real_git_owner.sh ]] || exit 2
W=$G/realgit4_by_swarm_opt; mkdir -p $W
for py in /usr/bin/python3 /scratch/jjyeung/envs/p1cpu/bin/python; do k=py36; [[ $py == *p1cpu* ]] && k=py312; mkdir -p $W/$k
  (cd $O && LCS_REVIEW2_FIXES=1 LCS_RUN_REAL_GIT_TESTS=1 LCS_REAL_GIT_WORK=$W/$k LCS_PYTHON=$py nice -n 10 timeout 900 bash tests/run_real_git_owner.sh > $W/run_$k.txt 2>&1; echo "rc=$?" >> $W/run_$k.txt)
done
tail -5 $W/run_*.txt | cut -c1-300; echo REALGIT_DONE > $W/DONE
