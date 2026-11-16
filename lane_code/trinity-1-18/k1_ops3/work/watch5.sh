#!/bin/bash
# waits up to $1 s (poll 300 s) for a new ORCH file, a native_r2 timing file, or inbox mail
EV=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
n0=$(ls $EV/k1_ops3 | grep -c '_ORCH_'); x0=$(ls $EV/native_r2 | grep -ciE "time|k1|h100|decode")
end=$(( $(date +%s) + $1 ))
while [ $(date +%s) -lt $end ]; do
  sleep 300
  [ $(ls $EV/k1_ops3 | grep -c '_ORCH_') -ne $n0 ] && { echo NEW_ORCH; ls $EV/k1_ops3 | grep '_ORCH_' | tail -1; exit 0; }
  [ $(ls $EV/native_r2 | grep -ciE "time|k1|h100|decode") -ne $x0 ] && { echo NATIVE_R2; ls -t $EV/native_r2 | head -3; exit 0; }
  ls /scratch/jjyeung/orch_n30/k1_ops3/inbox | grep -q . && { echo INBOX; exit 0; }
done
echo "no news $(date -u +%TZ)"
