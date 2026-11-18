#!/bin/bash
# cycles: m8.sh (yield check only) then SLEEP seconds; OURS from file ours_general.txt
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1orch
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops
for i in $(seq 1 ${1:-100}); do
  O=$(cat ours_general.txt 2>/dev/null)
  echo "=== cycle8 $i $(date -u +%TZ) OURS=$O" >> m8_hist.txt
  timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh "OURS='$O' N=${3:-2} bash -s" < m8.sh > m8.out 2>&1; cat m8.out >> m8_hist.txt
  if grep -q YIELD_CANCELLED m8.out; then
    S=$(date -u +%Y%m%dT%H%MZ); { echo "# RESULT cont_ops (watch loop8, $S): yielded general to main per ORCH ORDER 1359Z item 3"; grep YIELD_CANCELLED m8.out; echo "- Resubmit later with a fresh token when general shows no jjy_* job."; } > $E/${S}_RESULT_yield_general_cancelled.md
    : > ours_general.txt
  fi
  sleep ${2:-240}
done
