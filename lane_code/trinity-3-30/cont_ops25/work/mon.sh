#!/bin/bash
LOG=/scratch/jjyeung/orch_n30/cont_ops25/work/mon_173701.log
O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
for i in $(seq 1 90); do
  out=$(timeout 120 bash $O 'bash -s' < /scratch/jjyeung/orch_n30/cont_ops25/work/o_mon.sh 2>&1)
  echo "=== $(date -u +%H:%M:%SZ)" >> $LOG; echo "$out" | tail -c 1000 >> $LOG
  echo "$out" | grep -qE 'COMPLETED|FAILED|CANCELLED|TIMEOUT|OUT_OF_ME' && { echo DONE >> $LOG; break; }
  sleep 60
done
