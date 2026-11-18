#!/bin/bash
# cont_ops7 wait: up to $1 s (<=600); exits early on a new *_ORCH_* event or inbox file
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops; I=/scratch/jjyeung/orch_n30/cont_ops/inbox
S=/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/c7/seen.txt; touch $S
end=$(( $(date +%s) + ${1:-600} ))
while (( $(date +%s) < end )); do
  new=$( { ls -1 $E | grep _ORCH_; ls -1 $I; } | grep -v -x -F -f $S )
  [ -n "$new" ] && { echo "NEW: $new"; echo "$new" >> $S; exit 0; }
  sleep 30
done
echo "TICK $(date -u +%T)"
