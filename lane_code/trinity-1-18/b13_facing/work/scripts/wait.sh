#!/bin/bash
# Sleep up to $1 s (max 600); exit early when a new file appears in my events folder, my inbox, or events/cont_ops.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
L=/scratch/jjyeung/orch_n30/b13_facing; S=$L/work/seen.txt; touch $S
lst() { ls -1 $B/events/b13_facing/ | sed 's|^|b13/|'; ls -1 $L/inbox | sed 's|^|inbox/|'; ls -1 $B/events/cont_ops/ | grep -v '^STATUS.md$' | sed 's|^|cont/|'; }
END=$(( $(date +%s) + ${1:-600} ))
while [ $(date +%s) -lt $END ]; do
  new=$(lst | grep -v -x -F -f $S); if [ -n "$new" ]; then echo "$new"; echo "$new" >> $S; exit 0; fi
  sleep 60
done
echo "TICK $(date -u +%FT%TZ)"
