#!/bin/bash
# cont_ops17: reads monr_$J.log each minute (no ssh); if a jjy_* job pends on general, scancel J once and write a RESULT
LOG=/scratch/jjyeung/orch_n30/cont_ops/work/r1route/monr_$J.log; O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops
while true; do
  L=$(tail -1 $LOG 2>/dev/null)
  echo "$L" | grep -q LEFT_QUEUE && exit 0
  if echo "$L" | grep -q 'GQ jjy_'; then
    timeout 120 bash $O "scancel $J" >> $LOG.yield 2>&1; S=$(date -u +%Y%m%dT%H%MZ)
    printf '# RESULT cont_ops17: yielded general: scancel %s because a jjy_* job pends on general\n- %s\n' $J "$(echo "$L" | cut -c1-300)" > $E/${S}_RESULT_yield_general_cancelled_$J.md; exit 0
  fi
  sleep 60
done
