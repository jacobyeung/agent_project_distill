#!/bin/bash
# one Orchard check of 170525 then wait up to $1 min for new ORCH/inbox files
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1orch
timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < m1.sh > m1.out 2>&1; echo "ossh rc=$?"; cat m1.out >> m1_hist.txt
grep -v '^total\|^drwx' m1.out | head -20 | cut -c1-250
./w9.sh ${1:-9}
