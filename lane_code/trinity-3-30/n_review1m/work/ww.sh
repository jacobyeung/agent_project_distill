#!/bin/bash
# Wait up to $1 s (default 540) for a new file in inbox / events folders, or a stage change in watcher history. Checks every 60 s.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
M=/scratch/jjyeung/orch_n30/n_review1m
H=/scratch/jjyeung/orch_n30/n_ops1/work/mon/hist.txt
snap(){ { ls $M/inbox; ls $B/events/tree_rebuild; ls $B/events/n_review | grep -v STATUS; ls $B/events/n_ops | grep -v 'N_WATCH\|PROJECT_FS'; } 2>/dev/null | md5sum; }
st(){ tail -1 $H | grep -o 'job=[0-9]*\|"state":"[^"]*"\|"stage":"[^"]*"' | tr '\n' ' '; }
s0=$(snap); t0=$(st); end=$(( $(date +%s) + ${1:-540} ))
while [ $(date +%s) -lt $end ]; do
  sleep 60
  if [ "$(snap)" != "$s0" ]; then date -u +%TZ; echo NEWFILE; ls -t $M/inbox | head -2; for d in tree_rebuild n_review n_ops; do ls -t $B/events/$d | grep -v 'STATUS\|N_WATCH\|PROJECT_FS' | head -2; done; exit 0; fi
  if [ "$(st)" != "$t0" ]; then date -u +%TZ; echo "STAGE $t0 -> $(st)"; exit 0; fi
done
date -u +%TZ; echo "NONE $(st)"
