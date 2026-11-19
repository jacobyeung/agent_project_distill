#!/bin/bash
set -u
G=/scratch/jjyeung/orch_n30/so_git/work
for d in $(ls -dt $G/round2_validation_*/owner $G/round2_validation_*/*/owner 2>/dev/null); do [[ -f $d/tests/run_real_git_owner.sh ]] && { O=$d; break; }; done
echo "owner dir: ${O:-NONE}"; [[ -n "${O:-}" ]] || exit 2
W=$G/realgit2_by_swarm_opt; mkdir -p $W
for py in /usr/bin/python3 /scratch/jjyeung/envs/p1cpu/bin/python; do
  (cd $O && LCS_REVIEW2_FIXES=1 LCS_RUN_REAL_GIT_TESTS=1 LCS_REAL_GIT_WORK=$W/$(basename $(dirname $py)) LCS_PYTHON=$py nice -n 10 timeout 900 bash tests/run_real_git_owner.sh > $W/run_$(basename $(dirname $py)).txt 2>&1; echo "rc=$?" >> $W/run_$(basename $(dirname $py)).txt)
done
tail -5 $W/run_*.txt | cut -c1-300
