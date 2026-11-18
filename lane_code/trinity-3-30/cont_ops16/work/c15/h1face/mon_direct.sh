#!/bin/bash
# 1-min liveness monitor of the filtered step-544 read (J, TOK env); logs to mon_direct.log; exits when the job leaves the queue
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1read; O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
for i in $(seq 1 240); do
  R=$(timeout 120 bash $O "TZ=UTC squeue -j $J -h -o '%T %M %N %R'; ls /project/community/jjyeung/okh7/ae71c903/$TOK 2>/dev/null | tr '\n' ' '" 2>&1 | tr '\n' '|'); echo "$(date -u +%TZ) $R" >> mon_direct.log
  st=$(echo "$R" | grep -oE '^(RUNNING|PENDING|CONFIGURING|COMPLETING)')
  if [ -z "$st" ]; then st=$(timeout 120 bash $O "TZ=UTC sacct -j $J -X -n -o State" 2>&1 | awk 'NF{print $1; exit}'); echo "$(date -u +%TZ) sacct state=$st" >> mon_direct.log; fi
  case "$st" in RUNNING|PENDING|CONFIGURING|COMPLETING) ;; *) echo "$(date -u +%TZ) LEFT_QUEUE $st" >> mon_direct.log; : > ../h1orch/ours_general.txt; exit 0;; esac
  sleep 60
done
