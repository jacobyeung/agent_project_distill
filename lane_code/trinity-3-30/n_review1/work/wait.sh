#!/bin/bash
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; S=/scratch/jjyeung/orch_n30/n_review1
L(){ { ls -1 $B/events/tree_rebuild $B/events/n_review; ls -1 $S/inbox 2>/dev/null; } | grep -v '^STATUS.md$' | sort; }
L > $S/work/seen.now; [ -f $S/work/seen.base ] || cp $S/work/seen.now $S/work/seen.base
END=$(( $(date +%s) + ${1:-600} ))
while [ $(date +%s) -lt $END ]; do
  L > $S/work/seen.now; n=$(comm -13 $S/work/seen.base $S/work/seen.now)
  if [ -n "$n" ]; then echo "$n"; cp $S/work/seen.now $S/work/seen.base; exit 0; fi
  sleep 60
done; echo TIMEOUT
