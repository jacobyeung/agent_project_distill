#!/bin/bash
# 1-min monitor of $J with ORDER 2012Z deadline: cancel if PENDING at 21:03Z (cannot finish in 40 min) or still on general at 21:43Z
J=${J:?}; cd /scratch/jjyeung/orch_n30/cont_ops/work/h1read; O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
for i in $(seq 1 200); do
  now=$(date -u +%H%M)
  R=$(timeout 120 bash $O "TZ=UTC squeue -j $J -h -o '%T %M %N %R' 2>&1; ls -t /project/community/jjyeung/okh7/ae71c903/${TOK:?} 2>/dev/null | head -5 | tr '\n' ' '" 2>&1 | tr '\n' '|')
  echo "$(date -u +%TZ) $R" >> mon544.log
  st=$(echo "$R" | grep -oE '^(RUNNING|PENDING|CONFIGURING|COMPLETING)')
  if [ -z "$st" ]; then st=$(timeout 120 bash $O "TZ=UTC sacct -j $J -X -n -o State" 2>&1 | awk 'NF{print $1; exit}'); echo "$(date -u +%TZ) sacct state=$st" >> mon544.log; fi
  case "$st" in RUNNING|PENDING|CONFIGURING|COMPLETING) ;; *) echo "$(date -u +%TZ) LEFT_QUEUE" >> mon544.log; exit 0;; esac
  if { [ "$st" = PENDING ] && [ "$now" -ge 2103 ]; } || [ "$now" -ge 2143 ]; then
    timeout 120 bash $O "scancel $J; echo scancel rc=\$?" >> mon544.log 2>&1; echo "$(date -u +%TZ) DEADLINE_CANCEL state=$st" >> mon544.log; : > ../h1orch/ours_general.txt; exit 0
  fi
  sleep 60
done
