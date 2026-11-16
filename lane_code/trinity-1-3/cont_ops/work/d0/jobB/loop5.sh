#!/bin/bash
# One Orchard poll every 5 min (ORCH order 0729Z); output to p5_last.txt, history p5_hist.txt; max 36 polls (3 h).
D=/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB
for i in $(seq 36); do
  out=$(timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < $D/p5.sh 2>&1)
  echo "$out" > $D/p5_last.txt; { echo "######"; echo "$out"; } >> $D/p5_hist.txt
  sleep 300
done
