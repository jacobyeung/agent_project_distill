#!/bin/bash
# cont_ops18: monitor routed D job J (package P): 1-min, then 5-min after output lands; yield to jjy_* pending on general; graceful USR1 stop when the m400 export .done lands
set -u; O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops; LOG=/scratch/jjyeung/orch_n30/cont_ops18/monD_${J:?}.log
DONE=/project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m400.done; landed=0; signalled=0
for i in $(seq 1 400); do
  R=$(timeout 120 bash $O "TZ=UTC squeue -j $J -h -o 'ST %T %M %N %R'; test -s $DONE && echo DONE400; head -c 300 $P/a/x$J 2>/dev/null | head -1 | sed 's/^/X /'; echo POOLN \$(ls $P/a 2>/dev/null | wc -l); TZ=UTC squeue -p general -h -o 'GQ %j %T' | awk '\$2 ~ /^jjy_/ && \$3==\"PENDING\"'" 2>&1 | tr '\n' '|'); echo "$(date -u +%TZ) $R" >> $LOG
  st=$(echo "$R" | grep -oE 'ST (RUNNING|PENDING|CONFIGURING|COMPLETING)' | head -1 | cut -d' ' -f2)
  if [ -z "$st" ]; then st=$(timeout 120 bash $O "TZ=UTC sacct -j $J -X -n -o State,ExitCode,Elapsed,NodeList" 2>&1 | awk 'NF{print; exit}'); echo "$(date -u +%TZ) LEFT_QUEUE $st" >> $LOG
    S=$(date -u +%Y%m%dT%H%MZ); printf '# RESULT cont_ops18: routed D job %s left the queue: %s\n- Package %s; monitor log %s. Next: fetch, unpack, score_d.py.\n' $J "$st" $P $LOG > $E/${S}_RESULT_D_job_${J}_ended.md; exit 0; fi
  if echo "$R" | grep -q 'GQ jjy_\|DONE400'; then
    why=$(echo "$R" | grep -q DONE400 && echo "m400 export landed" || echo "a jjy_* job pends on general")
    if [ "$st" = PENDING ]; then timeout 120 bash $O "scancel $J" >> $LOG 2>&1; act="scancel (was pending)"
    elif [ $signalled = 0 ]; then timeout 120 bash $O "scancel --batch --signal=USR1 $J" >> $LOG 2>&1; signalled=1; act="USR1 graceful stop (running)"; else act=""; fi
    if [ -n "$act" ]; then S=$(date -u +%Y%m%dT%H%MZ); printf '# RESULT cont_ops18: yielded general: %s on D job %s because %s\n- %s\n' "$act" $J "$why" "$(echo "$R" | cut -c1-300)" > $E/${S}_RESULT_D_${J}_yield.md; fi
  fi
  [ $st = RUNNING ] && echo "$R" | grep -q '|X node' && landed=1
  [ $landed = 1 ] && sleep 300 || sleep 60
done
