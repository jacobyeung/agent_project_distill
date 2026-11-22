#!/bin/bash
# Poll NF-A GPU job: every 60 s for first 15 min, then every 300 s; exit on non-PENDING/RUNNING state change of interest or at 9.5 min wall.
T=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools
K=/scratch/jjyeung/orch_n30/lever7/nfa/kit
end=$(( $(date +%s) + ${1:-560} )); int=${2:-60}; last=""
while [ $(date +%s) -lt $end ]; do
  o=$(cd $K && timeout 120 bash $T/ossh.sh 'bash -s' < o_mon.sh 2>&1); st=$(printf '%s\n' "$o" | sed -n 1p | cut -d'|' -f2)
  if [ -z "$st" ]; then sleep 120; o=$(cd $K && timeout 120 bash $T/ossh.sh 'bash -s' < o_mon.sh 2>&1); st=$(printf '%s\n' "$o" | sed -n 1p | cut -d'|' -f2); [ -z "$st" ] && st=EMPTY_TWICE; fi
  echo "$(date -u +%H%MZ) $o" >> /scratch/jjyeung/orch_n30/lever8/work/mon_nfa.log
  [ "$st" != "$last" ] && echo "$(date -u +%H%MZ) $o"
  case "$st" in PENDING|RUNNING) ;; *) exit 0;; esac
  last=$st; sleep $int
done
