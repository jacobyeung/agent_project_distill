#!/bin/bash
# wait up to $1 s for a new event/inbox file or a new alert line (other than PROJECT_DISK alone), then run chk.sh (filtered)
W=/scratch/jjyeung/orch_n30; B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; L=$W/n_ops7; T=${1:-590}; s=0
SINCE=$(date -u -r $L/work/chk.since +%Y%m%dT%H%M%SZ)
while [ $s -lt $T ]; do
  n=$( (find $B/events/n_ops $B/events/tree_rebuild -maxdepth 1 -newer $L/work/chk.since -name '2026*'; find $L/inbox -newer $L/work/chk.since -type f) 2>/dev/null | wc -l)
  a=$(cat $W/n_ops1/work/mon/ALERTS.txt $W/n_ops2/work/mon2/ALERTS.txt 2>/dev/null | awk -v s=$SINCE '$1>s' | sed 's/FLAG PROJECT_DISK<150G//' | grep -c -E 'FLAG|STOP|BLOCK')
  g=$(tail -1 $W/n_ops1/work/mon/last.line | sed -n 's/.*"proj_free_G":\([0-9]*\).*/\1/p'); [ -n "$g" ] && [ "$g" -lt 50 ] && a=$((a+1))
  [ $((n+a)) -gt 0 ] && break; sleep 30; s=$((s+30)); done
bash $L/work/chk.sh 2>&1 | grep -v -E 'mon2 job=none' | cut -c1-500
