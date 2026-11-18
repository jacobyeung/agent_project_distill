#!/bin/bash
# Local loop (r1_ops3): one ossh status call every 70 s; keeps the newest output and a one-line history.
D=/scratch/jjyeung/orch_n30/r1_ops/work/drv_p5
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
cd "$D"
while [[ ! -e "$D/monloop.stop3" ]]; do
  timeout 300 bash "$OSSH" 'bash -s' < mon2.sh > mon2_tmp.txt 2>&1
  mv -f mon2_tmp.txt mon2_last.txt
  t=$(head -1 mon2_last.txt); s=$(grep -E "^1713(77|56)\|" mon2_last.txt | cut -d"|" -f1-5 | tr '\n' ' ')
  sz=$(grep -E '^== ' mon2_last.txt | awk '{print $2"="$3}' | tr '\n' ' ')
  echo "$t $s $sz" >> mon2_hist.txt
  sleep $(cat "$D/monloop.sleep" 2>/dev/null || echo 70)
done
