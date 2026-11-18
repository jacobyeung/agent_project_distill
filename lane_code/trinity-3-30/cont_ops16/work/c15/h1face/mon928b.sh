#!/bin/bash
# ORCH ANSWER 2129Z: keep 170928 until r1_ops2 posts *_RESULT_proof_ready_to_submit.md; then if answered >= 95% of 2169 allow at most 15 more min, else scancel at once
J=170928; cd /scratch/jjyeung/orch_n30/cont_ops/work/h1read; O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
R1=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/r1_ops; DL=""
for i in $(seq 1 300); do
  R=$(timeout 120 bash $O "TZ=UTC squeue -j $J -h -o '%T %M %N'" 2>&1 | tr '\n' '|'); echo "$(date -u +%TZ) $R DL=$DL" >> mon544.log
  st=$(echo "$R" | grep -oE '^(RUNNING|PENDING|CONFIGURING|COMPLETING)')
  if [ -z "$st" ]; then st=$(timeout 120 bash $O "TZ=UTC sacct -j $J -X -n -o State" 2>&1 | awk 'NF{print $1; exit}'); echo "$(date -u +%TZ) sacct state=$st" >> mon544.log; fi
  case "$st" in RUNNING|PENDING|CONFIGURING|COMPLETING) ;; *) echo "$(date -u +%TZ) LEFT_QUEUE $st" >> mon544.log; : > ../h1orch/ours_general.txt; exit 0;; esac
  if [ -z "$DL" ] && ls $R1/*_RESULT_proof_ready_to_submit.md >/dev/null 2>&1; then
    P=$(timeout 150 bash $O 'bash -s' < o_peek2.sh 2>&1); echo "$P" | sed 's/^/PEEK /' >> mon544.log
    F=$(echo "$P" | awk '/^LINES/{print $8}'); echo "$(date -u +%TZ) proof ready seen; answered frac=$F" >> mon544.log
    if [ -n "$F" ] && awk -v f=$F 'BEGIN{exit !(f>=0.95)}'; then DL=$(( $(date +%s) + 900 )); echo "$(date -u +%TZ) >=95%: deadline $(date -u -d @$DL +%TZ)" >> mon544.log
    else timeout 120 bash $O "scancel $J; echo scancel rc=\$?" >> mon544.log 2>&1; echo "$(date -u +%TZ) CANCEL_BELOW_95 frac=$F" >> mon544.log; : > ../h1orch/ours_general.txt; exit 0; fi
  fi
  if [ -n "$DL" ] && [ $(date +%s) -ge $DL ]; then timeout 120 bash $O "scancel $J; echo scancel rc=\$?" >> mon544.log 2>&1; echo "$(date -u +%TZ) CANCEL_15MIN_DEADLINE" >> mon544.log; : > ../h1orch/ours_general.txt; exit 0; fi
  sleep 60
done
