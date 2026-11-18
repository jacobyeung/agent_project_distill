#!/bin/bash
# local-only watcher: exits early on any change of interest; arg1 = max minutes
m=/scratch/jjyeung/orch_n30/r1_ops/work/drv_p5/mon2_last.txt
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/r1_ops
n0=$(ls $E | grep -c ORCH); end=$(( $(date +%s) + ${1:-30}*60 ))
while [[ $(date +%s) -lt $end ]]; do
  sleep 60
  r=""
  grep -q '^171377|a15_cot_ap673bc60f|advanced|RUNNING' $m || r="$r 171377-not-running"
  grep -E '673bc60f/m[0-9]+/' $m >/dev/null && r="$r export-files"
  [[ $(ls $E | grep -c ORCH) != $n0 ]] && r="$r new-ORCH"
  [[ -n "$(ls /scratch/jjyeung/orch_n30/r1_ops/inbox 2>/dev/null)" ]] && r="$r inbox"
  [[ -n "$(ls -t /scratch/jjyeung/orch_n30/r1_pkt/out/CONT4.md 2>/dev/null)" && ! -e /scratch/jjyeung/orch_n30/r1_ops/work/fs4/.c4bseen ]] && { touch /tmp/r1ops4_c4seen; r="$r CONT4"; }
  pgrep -f "label r1_cont4b" >/dev/null || { [[ -e /scratch/jjyeung/orch_n30/r1_ops/work/fs4/.c4bdone ]] || { touch /tmp/r1ops4_c4done; r="$r codex-c4-exited"; }; }
  [[ -n "$r" ]] && { echo "CHANGE:$r"; break; }
done
date -u +%T; head -1 $m; grep -E '^17(1377|2180)\|' $m | head -2; grep metrics $m
