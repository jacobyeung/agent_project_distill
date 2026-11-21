#!/bin/bash
# 1-minute launch watch for up to $1 s: every 60 s record the progress signature; stop early on two unchanged signatures in a row, a non-RUNNING state, a FLAG other than PROJECT_DISK, or a new ORCH/BLOCKER/QUESTION file
W=/scratch/jjyeung/orch_n30/n_ops10/work; M=/scratch/jjyeung/orch_n30/n_ops1/work/mon
O=/scratch/jjyeung/orch_n30; B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; SEEN=$W/seen.txt
lst() { ls $O/n_ops10/inbox $O/n_ops9/inbox $B/events/n_ops $B/events/tree_rebuild 2>/dev/null | grep -E 'SESS_JOB|ORCH|BLOCKER|QUESTION' | sort -u; }
end=$(( $(date +%s) + ${1:-540} )); prev=""; same=0; why=timeout
while [ $(date +%s) -lt $end ]; do
  l=$($W/sig.sh); echo "$l" >> $W/sig.log; s=$(echo "$l" | grep -o 'sig=[0-9a-f]*')
  if [ "$s" = "$prev" ]; then same=$((same+1)); else same=0; fi; prev=$s
  [ $same -ge 2 ] && { why="TWO_EMPTY_CHECKS"; break; }
  echo "$l" | grep -q 'RUNNING|' || { why="STATE: $l"; break; }
  fl=$(tail -1 $M/last.line | grep -o ' FLAG .*' | sed 's/ FLAG //; s/PROJECT_DISK<150G//; s/[ |]//g'); [ -n "$fl" ] && { why="FLAG: $(tail -1 $M/last.line | grep -o ' FLAG .*')"; break; }
  n=$(lst | comm -23 - <(sort -u $SEEN) | head -3); [ -n "$n" ] && { lst > $SEEN; why="NEW: $n"; break; }
  sleep 60
done
echo "END $why"; tail -4 $W/sig.log
