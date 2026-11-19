#!/bin/bash
# cont_ops19 (monR6 = monR + yield when the m600 export .done lands): monitor general job J (package P, label LB): 1-min, 5-min after output lands; scancel/USR1 if a jjy_* pends on general
# or when tree_rebuild12 posts in events/cont_ops that the proof takes general (file newer than start, name ~ proof|tree_rebuild, text ~ general, not ~ preempt-only/released)
set -u; O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops; LOG=/scratch/jjyeung/orch_n30/cont_ops19/work/monR_${J:?}.log
T0=/scratch/jjyeung/orch_n30/cont_ops19/work/.monR_t0_$J; touch $T0; landed=0; signalled=0
for i in $(seq 1 600); do
  R=$(timeout 120 bash $O "TZ=UTC squeue -j $J -h -o 'ST %T %M %N %R'; head -c 300 ${P:?}/a/x$J 2>/dev/null | head -1 | sed 's/^/X /'; TZ=UTC squeue -p general -h -o 'GQ %j %T' | awk '\$2 ~ /^jjy_/ && \$3==\"PENDING\"'; test -s /project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m600.done && echo DONE600" 2>&1 | tr '\n' '|')
  PR=""; for f in $(find $E -maxdepth 1 -newer $T0 -type f \( -iname '*proof*' -o -iname '*tree_rebuild*' \) 2>/dev/null); do
    grep -qi 'general' $f && ! grep -qi 'runs on preempt\|released general\|releases general\|not take general' $f && PR="PROOF $(basename $f)"; done
  echo "$(date -u +%TZ) $R $PR" >> $LOG
  st=$(echo "$R" | grep -oE 'ST (RUNNING|PENDING|CONFIGURING|COMPLETING)' | head -1 | cut -d' ' -f2)
  if [ -z "$st" ]; then sa=$(timeout 120 bash $O "TZ=UTC sacct -j $J -X -n -o State,ExitCode,Elapsed,NodeList" 2>&1 | awk 'NF{print; exit}')
    if echo "$sa" | grep -qE '^ *(COMPLETED|FAILED|CANCELLED|TIMEOUT|OUT_OF_ME|NODE_FAIL|PREEMPTED)'; then echo "$(date -u +%TZ) LEFT_QUEUE $sa" >> $LOG; exit 0; fi
    echo "$(date -u +%TZ) POLL_FAILED_OR_UNKNOWN $sa" >> $LOG; sleep 60; continue; fi
  if echo "$R" | grep -q 'GQ jjy_\|DONE600' || [ -n "$PR" ]; then
    why=$( [ -n "$PR" ] && echo "proof takes general ($PR)" || { echo "$R" | grep -q DONE600 && echo "m600 export landed"; } || echo "a jjy_* job pends on general")
    if [ "$st" = PENDING ]; then timeout 120 bash $O "scancel $J" >> $LOG 2>&1; act="scancel (was pending)"
    elif [ $signalled = 0 ]; then timeout 120 bash $O "scancel --batch --signal=USR1 $J" >> $LOG 2>&1; signalled=1; act="USR1 graceful stop (running)"; else act=""; fi
    if [ -n "$act" ]; then S=$(date -u +%Y%m%dT%H%MZ); printf '# RESULT cont_ops19: yielded general: %s on %s job %s because %s\n- %s\n' "$act" "${LB:-}" $J "$why" "$(echo "$R" | cut -c1-300)" > $E/${S}_RESULT_${LB:-job}_${J}_yield.md; fi
  fi
  [ "$st" = RUNNING ] && echo "$R" | grep -q '|X node' && landed=1
  [ $landed = 1 ] && sleep 300 || sleep 60
done
