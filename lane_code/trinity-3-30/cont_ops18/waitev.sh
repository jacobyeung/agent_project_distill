#!/bin/bash
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops; L=/scratch/jjyeung/orch_n30/cont_ops18
touch $L/.wmark; end=$(( $(date +%s) + ${1:-560} ))
while [ $(date +%s) -lt $end ]; do
  n=$(find $E -maxdepth 1 -newer $L/.wmark -type f \( -name '*ORCH*' -o -name '*QUESTION*' -o -name '*BLOCKER*' -o -name '*yield*' -o -name '*ended*' -o -name '*submitted*' \) | head -3)
  [ -n "$n" ] && { echo "EVENT: $n"; break; }
  tmux has-session -t chain400 2>/dev/null || { echo "chain400 GONE"; break; }
  sleep 30
done; date -u +%TZ; tail -1 $L/monD_172957.log | cut -c1-120
