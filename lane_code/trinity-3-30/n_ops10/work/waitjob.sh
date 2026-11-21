#!/bin/bash
# wait up to $1 s for a new (unseen by name) SESS_JOB/ORCH/BLOCKER/QUESTION file in my inboxes or events/n_ops, or for the job state to change; poll every 20 s
O=/scratch/jjyeung/orch_n30; B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; SEEN=$O/n_ops10/work/seen.txt
EV=$B/events/n_ops/N_WATCH_STATUS.md
touch $SEEN
lst() { ls $O/n_ops10/inbox $O/n_ops9/inbox $B/events/n_ops $B/events/tree_rebuild 2>/dev/null | grep -E 'SESS_JOB|_ORCH_|BLOCKER|QUESTION|[Ss]wap|n_ops10|resubmit|_held|RESULT.*(path|read|orchard)' | sort -u; }
st0=$(sed -n 4p $EV | grep -o 'state [A-Z]*')
end=$(( $(date +%s) + ${1:-540} ))
while [ $(date +%s) -lt $end ]; do
  n=$(lst | comm -23 - <(sort -u $SEEN) | head -3)
  [ -n "$n" ] && { echo "NEW: $n"; break; }
  st=$(sed -n 4p $EV | grep -o 'state [A-Z]*'); [ "$st" != "$st0" ] && { echo "STATE CHANGE: $st0 -> $st"; break; }
  sleep 20
done
lst > $SEEN
$O/n_ops10/work/chk.sh | grep -vE 'STATE_FAILED|CLEARED|BLOCKER_WRITTEN'
