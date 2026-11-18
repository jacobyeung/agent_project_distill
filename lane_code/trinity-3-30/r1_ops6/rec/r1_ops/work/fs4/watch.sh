#!/bin/bash
# local-only watcher: exits early on any change of interest; arg1 = max minutes
m=/scratch/jjyeung/orch_n30/r1_ops/work/drv_p5/mon2_last.txt
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/r1_ops
n0=$(ls $E | grep -c ORCH); end=$(( $(date +%s) + ${1:-30}*60 ))
while [[ $(date +%s) -lt $end ]]; do
  sleep 60
  r=""
  grep -q '^171377|a15_cot_ap673bc60f|advanced|RUNNING' $m || r="$r 171377-not-running"
  grep -E '673bc60f/m200/' $m >/dev/null && [[ ! -e /scratch/jjyeung/orch_n30/r1_ops/work/fs4/.m200seen ]] && { touch /scratch/jjyeung/orch_n30/r1_ops/work/fs4/.m200seen; r="$r m200"; }
  [[ $(ls $E | grep -c ORCH) != $n0 ]] && r="$r new-ORCH"
  [[ -n "$(ls /scratch/jjyeung/orch_n30/r1_ops/inbox 2>/dev/null)" ]] && r="$r inbox"
  [[ -n "$(ls -t /scratch/jjyeung/orch_n30/r1_pkt/out/CONT4.md 2>/dev/null)" && ! -e /scratch/jjyeung/orch_n30/r1_ops/work/fs4/.c4bseen ]] && { touch /tmp/r1ops4_c4seen; r="$r CONT4"; }
  [[ -e /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_r1anon7/STATUS.md.never && ! -e /scratch/jjyeung/orch_n30/r1_ops/work/fs4/.r1c3seen ]] && { touch /scratch/jjyeung/orch_n30/r1_ops/work/fs4/.r1c3seen; r="$r r1c3-verdict"; }
  grep -q "CHAIN2 DONE\|STOP\| rc=[1-9]" /scratch/jjyeung/orch_n30/r1_ops/work/drv_c1/chain2.log && [[ ! -e /scratch/jjyeung/orch_n30/r1_ops/work/fs4/.chain2seen ]] && { touch /scratch/jjyeung/orch_n30/r1_ops/work/fs4/.chain2seen; r="$r chain2"; }
  [[ -n "$(ls /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_r1anon7/ 2>/dev/null | grep RESULT)" && ! -e /scratch/jjyeung/orch_n30/r1_ops/work/fs4/.anon7seen ]] && { touch /scratch/jjyeung/orch_n30/r1_ops/work/fs4/.anon7seen; r="$r anon7"; }
  grep -qE "^172467\|(COMPLETED|FAILED|CANCELLED|TIMEOUT|OUT_OF)" $m && [[ ! -e /scratch/jjyeung/orch_n30/r1_ops/work/fs4/.rh1seen ]] && { touch /scratch/jjyeung/orch_n30/r1_ops/work/fs4/.rh1seen; r="$r rehearsal-ended"; }
  [[ -n "$r" ]] && { echo "CHANGE:$r"; break; }
done
date -u +%T; head -1 $m; grep -E '^17(1377|2180)\|' $m | head -2; grep metrics $m
