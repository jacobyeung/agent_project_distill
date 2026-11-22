#!/bin/bash
# wait up to $1 s (<=600) for a new ORCH event in events/lever or a file in lever9/inbox; print what is new.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/lever; L=/scratch/jjyeung/orch_n30/lever9
n0=$(ls $B | grep -c _ORCH_); i0=$(ls $L/inbox | wc -l); end=$(( $(date +%s) + ${1:-590} ))
while [ $(date +%s) -lt $end ]; do sleep 60
  n=$(ls $B | grep -c _ORCH_); i=$(ls $L/inbox | wc -l)
  if [ $n -ne $n0 ] || [ $i -ne $i0 ]; then date -u; ls $B | grep _ORCH_ | tail -2; ls $L/inbox; exit 0; fi
done; date -u; echo nothing_new; ls $B | tail -2
