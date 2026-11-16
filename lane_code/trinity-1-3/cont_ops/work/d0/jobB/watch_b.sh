#!/bin/bash
# Watch one Orchard job until it leaves PENDING; write exactly one event, then exit.
# Usage: watch_b.sh <jobid> [outdir]. Polls every 10 min through ossh.sh; exits after 30 h.
# ssh failure: wait 2 min, retry once; a second consecutive failure writes one BLOCKER event and exits.
J=${1:?jobid}
OUT=${2:-/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops}
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
LOG=/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/watch_b_$J.log
END=$(( $(date +%s) + 30*3600 ))
q() {
  timeout 300 bash $OSSH 'bash -s' <<EOF 2>&1
export TZ=UTC
s=\$(squeue -h -j $J -o '%T|%S|%N' 2>/dev/null | head -1)
[ -z "\$s" ] && s=\$(sacct -n -X -P -j $J -o State,Start,NodeList 2>/dev/null | head -1)
echo "STATE \$s"
EOF
}
while [ "$(date +%s)" -lt "$END" ]; do
  out=$(q); line=$(echo "$out" | grep '^STATE ' | tail -1)
  if [ -z "$line" ]; then
    echo "$(date -u +%FT%TZ) poll failed: $(echo "$out" | tail -2 | tr '\n' ' ')" >> $LOG
    sleep 120; out=$(q); line=$(echo "$out" | grep '^STATE ' | tail -1)
    if [ -z "$line" ]; then
      T=$(date -u +%Y%m%dT%H%MZ)
      { echo "From the job B state watcher (script on trinity-1-3, tmux watch_b_$J). Two consecutive Orchard polls of job $J failed at $(date -u +%FT%TZ); the watcher has exited."
        echo "Last output (2 lines): $(echo "$out" | tail -2 | tr '\n' ' ')"
        echo "Rule: LANE_RULES SSH/Orchard (one retry after 2 min; a second failure is a BLOCKER). Relaunch the watcher with: tmux new -d -s watch_b_$J 'bash $0 $J'"; } > "$OUT/${T}_BLOCKER_job_b_watcher_ssh.md"
      exit 2
    fi
  fi
  echo "$(date -u +%FT%TZ) $line" >> $LOG
  st=$(echo "${line#STATE }" | cut -d'|' -f1)
  if [ -n "$st" ] && [ "$st" != "PENDING" ]; then
    IFS='|' read -r S START NODE <<< "${line#STATE }"
    T=$(date -u +%Y%m%dT%H%MZ)
    { echo "From the job B state watcher (script on trinity-1-3, tmux watch_b_$J), $(date -u +%FT%TZ)."
      echo "Orchard job $J left PENDING: state $S, start $START (UTC), node ${NODE:-none}."
      echo "Question: launch the lane that babysits job B's first steps (cont_ops STATUS.md section 'Job B first steps')? The watcher has exited."; } > "$OUT/${T}_QUESTION_job_b_state_change.md"
    exit 0
  fi
  sleep 600
done
T=$(date -u +%Y%m%dT%H%MZ)
echo "From the job B state watcher: 30 h elapsed with job $J still PENDING at $(date -u +%FT%TZ); the watcher has exited." > "$OUT/${T}_QUESTION_job_b_watcher_expired.md"
