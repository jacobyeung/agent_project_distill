#!/bin/bash
# cont_ops20: after D@544 rem2 leaves the queue: fetch on Orchard, pull package (no a/e), score three segments
set -uo pipefail; W=/scratch/jjyeung/orch_n30/cont_ops20/work; O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh; PKG=a15_cot_apd5b7ea08426cd
timeout 300 bash $O 'bash -s' < $W/o_fetch_rem2.sh > $W/d3/fetch_rem2.out 2>&1 || { echo FETCH_FAILED; tail $W/d3/fetch_rem2.out; exit 2; }
cat $W/d3/fetch_rem2.out | head -c 1500; echo
timeout 300 bash $O "tar cf - -C /project/community/jjyeung/okh7 --exclude=$PKG/a/e $PKG" > $W/d3/rem2_pkg.tar || { echo PULL_FAILED; exit 2; }
mkdir -p $W/d3/p2 && tar xf $W/d3/rem2_pkg.tar -C $W/d3/p2 || exit 3
test -d /dev/shm/c19r/pkg2/a15_cot_apd09f959256d87 || { mkdir -p /dev/shm/c19r/pkg2 && tar xf /scratch/jjyeung/orch_n30/cont_ops19/work/drem1/pkg.tar -C /dev/shm/c19r/pkg2; }
cd $W && OPENBLAS_NUM_THREADS=1 /scratch/jjyeung/envs/p1cpu/bin/python -B score_d3.py --spec d3/SPEC544.json --work /dev/shm/c20d3_$(date +%H%M%S) --out d3/SCORES_D544_merged.json
