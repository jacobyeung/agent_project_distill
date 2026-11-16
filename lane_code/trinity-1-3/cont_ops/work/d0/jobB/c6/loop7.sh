#!/bin/bash
# cont_ops6: watch poll of job B every 10 min (q3.sh), 30 polls max (~5 h)
D=/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/c6; T=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools
for i in $(seq 1 30); do
  timeout 300 bash $T/ossh.sh 'bash -s' < $D/q3.sh > $D/q3.tmp 2>&1; rc=$?
  { echo "#### $(date -u +%FT%TZ) poll $i rc=$rc"; cat $D/q3.tmp; } >> $D/q3_hist.txt; mv $D/q3.tmp $D/q3.out
  sleep 600
done
