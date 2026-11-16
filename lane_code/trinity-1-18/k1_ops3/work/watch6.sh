#!/bin/bash
EV=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
n0=$(ls $EV/k1_ops3 | grep -c '_ORCH_'); x0=$(ls $EV/native_r2 | grep -ciE "time|k1|h100|decode")
end=$(( $(date +%s) + $1 ))
while [ $(date +%s) -lt $end ]; do
  sleep 300
  pgrep -u jjyeung -f 'codex exec -m gpt-6-astra.*partb' >/dev/null || { echo CODEX_DONE; exit 0; }
  [ $(ls $EV/k1_ops3 | grep -c '_ORCH_') -ne $n0 ] && { echo NEW_ORCH; ls $EV/k1_ops3 | grep '_ORCH_' | tail -1; exit 0; }
  [ $(ls $EV/native_r2 | grep -ciE "time|k1|h100|decode") -ne $x0 ] && { echo NATIVE_R2; ls -t $EV/native_r2 | head -3; exit 0; }
done
