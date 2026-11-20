#!/bin/bash
LOG=/scratch/jjyeung/orch_n30/cont_ops24/work/mon_cpu.log
for i in $(seq 1 120); do
  out=$(timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < /dev/shm/c24/o_mon.sh 2>&1)
  echo "=== $(date -u +%H:%M:%SZ)" >> $LOG; echo "$out" | tail -c 1200 >> $LOG
  echo "$out" | grep -q "173603 a15" || { echo "LEFT_QUEUE" >> $LOG; break; }
  sleep 60
done
