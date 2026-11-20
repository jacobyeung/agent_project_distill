#!/bin/bash
# wait up to $1 s (default 590) for a new event/inbox/alert, then run chk.sh (filtered)
W=/scratch/jjyeung/orch_n30; B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; L=$W/n_ops4; T=${1:-590}; s=0
while [ $s -lt $T ]; do
  n=$( (find $B/events/n_ops $B/events/tree_rebuild $B/events/n_review -maxdepth 1 -newer $L/work/chk.since -name '2026*'; find $L/inbox -newer $L/work/chk.since -type f; find $W/n_ops1/work/mon/ALERTS.txt $W/n_ops2/work/mon2/ALERTS.txt -newer $L/work/chk.since) 2>/dev/null | wc -l)
  [ $n -gt 0 ] && break; sleep 30; s=$((s+30)); done
bash $L/work/chk.sh 2>&1 | grep -v -E '^2026.*(FAILED|CANCELLED)' | grep -v -E 'mon2 job=none|job=173568' | cut -c1-400
