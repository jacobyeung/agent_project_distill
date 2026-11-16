#!/bin/bash
# waits up to $1 seconds, polling every 300 s; returns early on run end, stall, new ORCH file, review_k1g verdict or native_r2 new file
EV=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
n0=$(ls $EV/k1_ops3 | grep -c ORCH); r0=$(ls $EV/review_k1g 2>/dev/null | wc -l); x0=$(ls $EV/native_r2 | grep -ciE "time|k1|h100")
end=$(( $(date +%s) + $1 ))
while [ $(date +%s) -lt $end ]; do
  sleep 300
  python3 /scratch/jjyeung/orch_n30/k1_ops3/work/prog2b.py | head -1
  grep -qE '^EXIT|STOP written' /scratch/jjyeung/k1/RUN2b.log && { echo RUN_END; grep -E 'EXIT|STOP' /scratch/jjyeung/k1/RUN2b.log; exit; }
  [ -s /scratch/jjyeung/k1/STALL2b.log ] && { echo STALL; cat /scratch/jjyeung/k1/STALL2b.log; exit; }
  [ $(ls $EV/k1_ops3 | grep -c ORCH) -ne $n0 ] && { echo NEW_ORCH; ls $EV/k1_ops3 | grep ORCH | tail -1; exit; }
  [ $(ls $EV/review_k1g 2>/dev/null | wc -l) -ne $r0 ] && { echo REVIEW_K1G; ls -t $EV/review_k1g | head -3; exit; }
  [ $(ls $EV/native_r2 | grep -ciE "time|k1|h100") -ne $x0 ] && { echo NATIVE_R2; ls -t $EV/native_r2 | head -2; exit; }
  ls /scratch/jjyeung/orch_n30/k1_ops3/inbox | grep -q . && { echo INBOX; ls /scratch/jjyeung/orch_n30/k1_ops3/inbox; exit; }
done
