#!/bin/bash
# Wait up to $1 s (checks every 290 s) for any new file in events/tree_rebuild, events/n_review, events/n_ops or my inbox.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
I=/scratch/jjyeung/orch_n30/n_review1l/inbox
S=/scratch/jjyeung/orch_n30/n_review1l/work/seen.txt
list(){ for d in tree_rebuild n_review n_ops; do ls $B/events/$d 2>/dev/null | grep -E '^2026' | sed "s|^|$d/|"; done; ls $I 2>/dev/null | sed 's/^/INBOX\//'; }
[ -f $S ] || list | sort > $S
end=$(( $(date +%s) + ${1:-570} ))
while :; do
  new=$(comm -13 $S <(list | sort) | grep -v "^n_review/.*_RESULT_")
  if [ -n "$new" ]; then date -u +%H:%MZ; echo "$new"; list | sort > $S; exit 0; fi
  [ $(( $(date +%s) + 290 )) -gt $end ] && break
  sleep 290
done
date -u +%H:%MZ; echo NONE
