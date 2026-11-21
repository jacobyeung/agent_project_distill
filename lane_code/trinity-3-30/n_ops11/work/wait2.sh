#!/bin/bash
# wait up to $1 s; stop on: a new file in my inbox; a new ORCH file in events/n_ops|tree_rebuild whose first line names n_ops11; a new BLOCKER or name with n_ops11/SESS/held/submit in those folders; a job state change or a new job in MON/job
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; O=/scratch/jjyeung/orch_n30; M=$O/n_ops1/work/mon; W=$O/n_ops11/work
lst() { for d in $B/events/n_ops $B/events/tree_rebuild; do ls $d | sed "s#^#$d/#"; done | sort -u; }
[ -s $W/seen3.txt ] || lst > $W/seen3.txt; ls $O/n_ops11/inbox | sort > $W/inbox_seen.txt
st0=$(tail -1 $M/hist.txt | grep -o '"state":"[A-Z]*"'); j0=$(cat $M/job); end=$(( $(date +%s) + ${1:-530} )); why=timeout
while [ $(date +%s) -lt $end ]; do
  hit=""
  for f in $(lst | comm -23 - $W/seen3.txt); do b=$(basename $f)
    case $b in *_ORCH_*) head -1 $f | grep -q n_ops11 && hit="$hit $b";; *BLOCKER*|*n_ops11*|*SESS*|*sess*|*_held_*|*held_on*|*submit*) hit="$hit $b";; esac; done
  lst > $W/seen3.txt
  ni=$(ls $O/n_ops11/inbox | sort | comm -23 - $W/inbox_seen.txt); [ -n "$ni" ] && hit="$hit INBOX:$ni"
  [ -n "$hit" ] && { why="NEW:$hit"; break; }
  st=$(tail -1 $M/hist.txt | grep -o '"state":"[A-Z]*"'); [ "$st" != "$st0" ] && { why="STATE $st0 -> $st"; break; }
  [ "$(cat $M/job)" != "$j0" ] && { why="MON/job $j0 -> $(cat $M/job)"; break; }
  sleep 60
done
echo "END $why"; tail -1 $M/hist.txt | cut -c1-200
