#!/bin/bash
# wait up to $1 s; stop on a new file in my inbox, events/n_ops, events/tree_rebuild*, SESS_JOB, or a state change in last.line
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; O=/scratch/jjyeung/orch_n30; M=$O/n_ops1/work/mon; W=$O/n_ops11/work
lst() { ls $O/n_ops11/inbox $O/n_ops10/inbox $B/events/n_ops $B/events/tree_rebuild $B/events/n_review 2>/dev/null | grep -vE '^N_WATCH|^STATUS|^PROJECT_FS|^$|:$' | sort -u; }
[ -s $W/seen2.txt ] || lst > $W/seen2.txt
st0=$(tail -1 $M/hist.txt | grep -o '"state":"[A-Z]*"'); end=$(( $(date +%s) + ${1:-540} )); why=timeout
while [ $(date +%s) -lt $end ]; do
  n=$(lst | comm -23 - $W/seen2.txt); lst > $W/seen2.txt; n=$(echo "$n" | grep -E "_ORCH_|SESS_JOB|n_ops11|BLOCKER|resubmit|held|_sess" ; ls $O/n_ops11/inbox | comm -23 - <(sort -u $W/inbox_seen.txt 2>/dev/null)); [ -n "$n" ] && { lst > $W/seen2.txt; ls $O/n_ops11/inbox | sort > $W/inbox_seen.txt; why="NEW: $n"; break; }
  st=$(tail -1 $M/hist.txt | grep -o '"state":"[A-Z]*"'); [ "$st" != "$st0" ] && { why="STATE $st0 -> $st"; break; }
  sleep 60
done
echo "END $why"; tail -1 $M/hist.txt | cut -c1-200
