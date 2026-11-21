#!/bin/bash
# Wait up to $1 seconds (default 300) for a new file in tree_rebuild events, n_review events, or my inbox.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
snap(){ ls $B/events/tree_rebuild $B/events/n_review /scratch/jjyeung/orch_n30/n_review1j/inbox 2>/dev/null | grep -v STATUS.md | md5sum; }
a=$(snap); end=$(( $(date +%s) + ${1:-300} ))
while [ $(date +%s) -lt $end ]; do sleep 30; [ "$(snap)" != "$a" ] && break; done
date -u +%H:%MZ; ls -t $B/events/tree_rebuild | head -4; echo; ls -t $B/events/n_review | head -4; echo; ls -t /scratch/jjyeung/orch_n30/n_review1j/inbox | head -3
