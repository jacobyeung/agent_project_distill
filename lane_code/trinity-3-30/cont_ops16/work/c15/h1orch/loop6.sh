#!/bin/bash
# cycles of m5.sh (N internal 30 s polls) then SLEEP seconds
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1orch
for i in $(seq 1 ${1:-100}); do
  echo "=== cycle6 $i $(date -u +%TZ)" >> m1_hist.txt
  N=${3:-2} timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh "N=${3:-2} bash -s" < m5.sh > m5.out 2>&1; cat m5.out >> m1_hist.txt
  sleep ${2:-480}
done
