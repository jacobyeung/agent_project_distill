#!/bin/bash
# poll rp.sh every ~65 s; exit when 172476 not PENDING or after $1 polls
W=/scratch/jjyeung/orch_n30/r1_ops/work/fs5; O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
for i in $(seq 1 ${1:-10}); do
  sleep 65
  timeout 120 bash $O 'bash -s' < $W/rp.sh > $W/rp_last.out 2>&1
  cat $W/rp_last.out >> $W/rp_hist.out
  grep -q '^172476|PENDING' $W/rp_last.out || { cat $W/rp_last.out; exit 0; }
done
cat $W/rp_last.out
