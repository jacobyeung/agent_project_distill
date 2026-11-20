#!/bin/bash
set -u; O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh; LOG=/scratch/jjyeung/orch_n30/cont_ops24/work/monG_${J:?}.log
for i in $(seq 1 700); do
  R=$(timeout 120 bash $O "TZ=UTC squeue -j $J -h -o 'ST %P %T %M %N %R'; sstat -j $J.batch -n -P --format=AveCPU,MaxRSS,MaxDiskRead,MaxDiskWrite 2>/dev/null" 2>&1 | tr '\n' '|'); echo "$(date -u +%TZ) $R" >> $LOG
  if ! echo "$R" | grep -qE 'ST [a-z]+ (RUNNING|PENDING|CONFIGURING|COMPLETING)'; then sa=$(timeout 120 bash $O "TZ=UTC sacct -j $J -X -n -o State,ExitCode,Elapsed,NodeList,Partition" 2>&1 | awk 'NF{print; exit}')
    echo "$sa" | grep -qE '^ *(COMPLETED|FAILED|CANCELLED|TIMEOUT|OUT_OF_ME|NODE_FAIL|PREEMPTED)' && { echo "$(date -u +%TZ) LEFT_QUEUE $sa" >> $LOG; exit 0; }; fi
  sleep 60; done
