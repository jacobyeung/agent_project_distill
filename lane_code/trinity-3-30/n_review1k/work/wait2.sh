#!/bin/bash
# Wait up to $1 s for a new event relevant to n_review1k (name or content mentions it, WAITING_REVIEW, BLOCKER, FAIL, gate) or a new inbox file.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
I=/scratch/jjyeung/orch_n30/n_review1k/inbox
list(){ ls $B/events/tree_rebuild $B/events/n_review $B/events/n_ops 2>/dev/null | grep -E '^2026' | sort; ls $I 2>/dev/null | sed 's/^/INBOX /' | sort; }
a=$(list); end=$(( $(date +%s) + ${1:-1800} ))
while [ $(date +%s) -lt $end ]; do sleep 30
  if grep -q -i 'WAITING_REVIEW\|waiting review\|stage gate\|stage review' $B/events/n_ops/N_WATCH_STATUS.md 2>/dev/null; then date -u +%H:%MZ; echo "HIT: N_WATCH_STATUS mentions WAITING_REVIEW"; grep -i 'job 174198\|WAITING' $B/events/n_ops/N_WATCH_STATUS.md | head -3; exit 0; fi
  b=$(list); new=$(comm -13 <(echo "$a") <(echo "$b")); a=$b
  [ -z "$new" ] && continue
  hit=""; for f in $new; do
    [ "$f" = INBOX ] && continue
    case "$f" in *n_review1k*|*WAITING*|*BLOCKER*|*FAIL*|*gate*|*review*|*rehearsal*|*ORCH*|*H_*) hit="$hit $f";; esac
    for d in tree_rebuild n_review n_ops; do [ -f $B/events/$d/$f ] && grep -q -E 'n_review1k|WAITING_REVIEW' $B/events/$d/$f 2>/dev/null && hit="$hit $f"; done
  done
  echo "$new" | grep -q '^INBOX' && hit="$hit inbox"
  [ -n "$hit" ] && { date -u +%H:%MZ; echo "HIT:$hit"; echo "$new"; exit 0; }
done
date -u +%H:%MZ; echo "TIMEOUT no relevant event"
