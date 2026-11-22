#!/bin/bash
# n_ops12 waiter: up to $1 s (<=300). Stops on a new file in events/n_ops|tree_rebuild|n_review (not STATUS/N_WATCH*/PROJECT_FS), a new inbox file, job state change, MON/job change, stale watcher.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; O=/scratch/jjyeung/orch_n30; M=$O/n_ops1/work/mon; W=$O/n_ops12/work
lst() { for d in $B/events/n_ops $B/events/tree_rebuild $B/events/n_review; do ls $d | grep -v -e '^STATUS.md$' -e '^N_WATCH' -e '^PROJECT_FS' | sed "s#^#$(basename $d)/#"; done | sort -u; ls $O/n_ops12/inbox | sed 's#^#INBOX/#'; }
[ -s $W/seen.txt ] || lst | sort > $W/seen.txt
st0=$(tail -1 $M/hist.txt | grep -o '"state":"[A-Z]*"'); j0=$(cat $M/job); end=$(( $(date +%s) + ${1:-290} )); why=timeout
while [ $(date +%s) -lt $end ]; do
  new=$(lst | sort | comm -23 - $W/seen.txt); lst | sort > $W/seen.txt; new=$(echo "$new" | grep -E "INBOX/|_ORCH_|BLOCKER|SESS|n_ops12|held_on|submit|sess|rotate|project|wrote"); [ -n "$new" ] && { why="NEW: $new"; lst | sort > $W/seen.txt; break; }
  st=$(tail -1 $M/hist.txt | grep -o '"state":"[A-Z]*"'); [ "$st" != "$st0" ] && { why="STATE $st0 -> $st"; break; }
  [ "$(cat $M/job)" != "$j0" ] && { why="MON/job $j0 -> $(cat $M/job)"; break; }
  [ $(( $(date +%s) - $(stat -c %Y $M/hist.txt) )) -gt 300 ] && { why="WATCHER STALE"; break; }
  sleep 30
done
echo "END $(date -u +%H:%M:%SZ) $why"; tail -1 $M/hist.txt | cut -c1-120; grep -o '"stage":"[a-z_A-Z0-9]*"' <(tail -1 $M/hist.txt)
