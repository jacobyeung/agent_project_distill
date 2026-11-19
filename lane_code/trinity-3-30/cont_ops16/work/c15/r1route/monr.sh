#!/bin/bash
# cont_ops16: 1-min monitor of a routed-read Orchard job (J, PK=package token, LOG); exits when J leaves the queue
O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh; LOG=/scratch/jjyeung/orch_n30/cont_ops/work/r1route/monr_$J.log
for i in $(seq 1 ${N:-400}); do
  R=$(timeout 120 bash $O "TZ=UTC squeue -j $J -h -o 'ST %T %M %N %R'; ls /project/community/jjyeung/okh7/a15_cot_ap$PK/a | tr '\n' ' '; TZ=UTC squeue -p general -h -o 'GQ %j %T' | awk '\$2 ~ /^jjy_/ && \$3==\"PENDING\"'" 2>&1 | tr '\n' '|'); echo "$(date -u +%TZ) $R" >> $LOG
  st=$(echo "$R" | grep -oE 'ST (RUNNING|PENDING|CONFIGURING|COMPLETING)' | head -1)
  if [ -z "$st" ]; then echo "$(date -u +%TZ) LEFT_QUEUE $(timeout 120 bash $O "TZ=UTC sacct -j $J -X -n -o State,ExitCode,Elapsed" 2>&1 | awk 'NF{print; exit}')" >> $LOG; exit 0; fi
  sleep ${SLEEP:-60}
done
