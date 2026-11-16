#!/bin/bash
cd /scratch/jjyeung/orch_n30/gpu_fill
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/gpu_fill
ls $E > seen_ev.txt
while [ $(date -u +%H%M) -lt 2245 ]; do
  ./tick.sh > /dev/null 2>&1
  J=$(ls -t hist/2*.json | head -1)
  python3 alert.py $J | sed "s/^/$(date -u +%H%MZ) /" >> alerts.log
  ls $E > cur_ev.txt; comm -13 seen_ev.txt cur_ev.txt | grep -E 'ORCH' | sed "s/^/$(date -u +%H%MZ) NEWEVENT /" >> alerts.log; mv cur_ev.txt seen_ev.txt
  [ -f /data2/jjyeung/agent_project_data/distill_design/NEXT_QUEUE_20261116.md ] && [ ! -f queue_seen ] && { touch queue_seen; echo "$(date -u +%H%MZ) NEXT_QUEUE landed" >> alerts.log; }
  echo "$(date -u +%H%MZ) tick" >> alerts.log
  sleep 600
done
echo "$(date -u +%H%MZ) LOOP_END" >> alerts.log
