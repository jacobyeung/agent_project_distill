#!/bin/bash
# exits when a new *_ORCH_* event or inbox file appears, or after $1 seconds
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops; I=/scratch/jjyeung/orch_n30/cont_ops/inbox
a=$(ls $E | grep _ORCH_ | sort | tail -1); b=$(ls $I | sort | tail -1); end=$(( $(date +%s) + ${1:-3600} ))
while [ $(date +%s) -lt $end ]; do
  sleep 120
  x=$(ls $E | grep _ORCH_ | sort | tail -1); y=$(ls $I | sort | tail -1)
  [ "$x" != "$a" ] && { echo "NEW ORCH $x"; exit 0; }
  [ "$y" != "$b" ] && { echo "NEW INBOX $y"; exit 0; }
done; echo "TIMEOUT $(date -u +%TZ)"
