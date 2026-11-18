#!/bin/bash
# Poll A2 stage 2 every 10 min; exit when s2.json exists or 170109 leaves RUNNING; max 20 polls.
for i in $(seq 20); do
  out=$(timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < /scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/w2c.sh 2>&1)
  echo "$out" > /scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/w2_last.txt
  if echo "$out" | grep -q '170109\.s2\.json' || ! echo "$out" | grep -q '^170109 RUNNING'; then echo "$out"; exit 0; fi
  sleep 600
done
