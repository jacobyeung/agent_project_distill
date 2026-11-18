#!/bin/bash
# cont_ops16: 1-min liveness + output + yield monitor (J, TOK env); log mon16_$TOK.log; scancel J at once if a jjy_* job pends on general; exits when J leaves the queue
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1vsti; O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops; LOG=mon16_$TOK.log
for i in $(seq 1 ${N:-300}); do
  R=$(timeout 120 bash $O "TZ=UTC squeue -j $J -h -o 'ST %T %M %N %R'; echo POOL \$(ls -la /project/community/jjyeung/okh7/ae71c903/$TOK 2>/dev/null | awk 'NR>3{print \$5\":\"\$9}' | tr '\n' ' '); TZ=UTC squeue -p general -h -o 'GQ %j %T %r' | awk '\$2 ~ /^jjy_/ && \$3==\"PENDING\"'" 2>&1 | tr '\n' '|'); echo "$(date -u +%TZ) $R" >> $LOG
  if echo "$R" | grep -q 'GQ jjy_'; then
    timeout 120 bash $O "scancel $J" >> $LOG 2>&1; S=$(date -u +%Y%m%dT%H%MZ)
    printf '# RESULT cont_ops16: yielded general: scancel %s (token %s) because a jjy_* job pends on general\n- %s\n- Token spent; re-prepare with a fresh token when general shows no jjy_* job.\n' $J $TOK "$(echo "$R" | tr '|' ' ' | cut -c1-300)" > $E/${S}_RESULT_yield_general_cancelled_$J.md; exit 0; fi
  st=$(echo "$R" | grep -oE 'ST (RUNNING|PENDING|CONFIGURING|COMPLETING)' | head -1)
  if [ -z "$st" ]; then st=$(timeout 120 bash $O "TZ=UTC sacct -j $J -X -n -o State,ExitCode,Elapsed" 2>&1 | awk 'NF{print; exit}'); echo "$(date -u +%TZ) LEFT_QUEUE $st" >> $LOG; exit 0; fi
  sleep ${SLEEP:-60}
done
