#!/bin/bash
# poll Orchard every 120 s until job leaves PENDING/RUNNING; max 50 polls
for i in $(seq 50); do
  out=$(timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < /scratch/jjyeung/orch_n30/lever5/work/mong.sh 2>&1 | tail -1)
  echo "$out" >> /scratch/jjyeung/orch_n30/lever5/work/wait_job.log
  echo "$out" | grep -q -E 'RUNNING|PENDING' || { echo "DONE: $out"; exit 0; }
  sleep 120
done
