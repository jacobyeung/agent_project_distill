#!/bin/bash
W=/scratch/jjyeung/orch_n30/cont_ops24/work; LOG=$W/monP_${J}.log; sed "s/__J__/$J/g" $W/o_prog.sh > /dev/shm/c24/o_prog_$J.sh
for i in $(seq 1 60); do
  out=$(timeout 200 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < /dev/shm/c24/o_prog_$J.sh 2>&1)
  echo "=== $(date -u +%H:%M:%SZ) $out" >> $LOG
  grep -q LEFT_QUEUE $W/monG_${J}.log 2>/dev/null && break
  sleep ${STEP:-300}
done
