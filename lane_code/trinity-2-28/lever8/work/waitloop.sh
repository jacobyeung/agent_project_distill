#!/bin/bash
# Tick every 10 min; exit when 174328 leaves PENDING, an ORCH answer to lever8 lands, or the inbox fills. Max ~6 ticks.
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/lever
n0=$(ls $E | grep -c 'ORCH')
for i in 1 2 3 4 5 6; do
  sleep 600
  out=$(bash /scratch/jjyeung/orch_n30/lever8/work/tick.sh 2>&1)
  echo "$out" > /scratch/jjyeung/orch_n30/lever8/work/last_tick.txt
  n=$(ls $E | grep -c 'ORCH')
  if ! echo "$out" | grep -q "^174328 .*${1:-PENDING}" || [ "$n" != "$n0" ] || [ -n "$(ls /scratch/jjyeung/orch_n30/lever8/inbox)" ]; then echo "$out"; exit 0; fi
done
echo "$out"
