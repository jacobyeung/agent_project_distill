#!/bin/bash
# Poll A2 every 10 min (one ossh call); stop when the stop pattern appears in a.steps or the job leaves RUNNING.
PAT=${1:-mode p exit}
for i in $(seq 40); do
  out=$(timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < /scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/w1.sh 2>&1)
  echo "$out" > /scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/watch_last.txt
  if echo "$out" | grep -q "$PAT" || ! echo "$out" | grep -q " RUNNING "; then echo "$out"; exit 0; fi
  sleep 600
done
