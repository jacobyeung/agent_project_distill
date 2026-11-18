#!/bin/bash
# like waitorch.sh, plus exits when file $2 appears
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops; I=/scratch/jjyeung/orch_n30/cont_ops/inbox
a=$(ls $E | grep _ORCH_ | sort | tail -1); b=$(ls $I | sort | tail -1); end=$(( $(date +%s) + ${1:-3600} ))
while [ $(date +%s) -lt $end ]; do
  sleep 60
  [ -n "${2:-}" ] && [ -e "$2" ] && { echo "FILE $2"; exit 0; }
  x=$(ls $E | grep _ORCH_ | sort | tail -1); y=$(ls $I | sort | tail -1)
  [ "$x" != "$a" ] && { echo "NEW ORCH $x"; exit 0; }
  [ "$y" != "$b" ] && { echo "NEW INBOX $y"; exit 0; }
done; echo "TIMEOUT $(date -u +%TZ)"
