#!/bin/bash
# cont_ops21 monA5 (= monA3 with sacct-confirmed exit): monitor advanced jobs JOBS="j1 j2 j3" (1-min); yield (USR1 if running, scancel if pending) on N's launch GO:
# a new file in events/cont_ops whose name contains launch and (GO|submitted|pending) (ORDER 1721Z item 2). Writes one RESULT line on yield.
set -u; O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops; W=/scratch/jjyeung/orch_n30/cont_ops21/work
LOG=/scratch/jjyeung/orch_n30/cont_ops22/work/monB2.log; T0=/scratch/jjyeung/orch_n30/cont_ops22/work/.monB2_t0; [ -e $T0 ] || touch $T0; yielded=0; J=${JOBS:?}
for i in $(seq 1 600); do
  R=$(timeout 120 bash $O "TZ=UTC squeue -j ${J// /,} -h -o 'ST %i %T %M %N %R'" 2>&1 | tr '\n' '|')
  GO=$(find $E -maxdepth 1 -newer $T0 -type f -iname '*launch*' 2>/dev/null | grep -E 'ORCH_.*(GO|go)|launch.*(submitted|pending)|(submitted|pending).*launch' | grep -viE 'review|kit|fixture' | head -1)
  echo "$(date -u +%TZ) $R ${GO:+LAUNCH $(basename $GO)}" >> $LOG
  if [ -n "$GO" ] && [ $yielded = 0 ] && echo "$R" | grep -q "ST [0-9]"; then
    for j in $J; do st=$(echo "$R" | grep -oE "ST $j [A-Z]+" | awk '{print $3}')
      [ "$st" = PENDING ] && timeout 120 bash $O "scancel $j" >> $LOG 2>&1
      [ "$st" = RUNNING ] && timeout 120 bash $O "scancel --batch --signal=USR1 $j" >> $LOG 2>&1; done
    yielded=1; sleep 30; Q=$(timeout 120 bash $O "TZ=UTC squeue -u jjyeung -p advanced -h -o '%i %j %T'" 2>&1 | tr '\n' ' ')
    printf '# RESULT cont_ops22: advanced yielded for the launch (%s): USR1/scancel sent to %s; advanced now holds: %s\n' "$(basename $GO)" "$J" "$Q" > $E/$(date -u +%Y%m%dT%H%MZ)_RESULT_advanced_yield_for_N_d.md
  fi
  if [ -z "$(echo "$R" | grep -oE 'ST [0-9]+ (RUNNING|PENDING|CONFIGURING|COMPLETING)')" ]; then
    SA=$(timeout 120 bash $O "TZ=UTC sacct -j ${J// /,} -X -n -o JobID,State" 2>&1 | tr '\n' '|'); echo "$(date -u +%TZ) SACCT $SA" >> $LOG
    n=$(echo "$SA" | grep -oE '[0-9]+ +(COMPLETED|FAILED|CANCELLED[^|]*|TIMEOUT|OUT_OF_ME[A-Z]*|NODE_FAIL|PREEMPTED)' | wc -l)
    [ "$n" -eq $(echo $J | wc -w) ] && { echo "$(date -u +%TZ) ALL_LEFT" >> $LOG; exit 0; }
  fi
  sleep 60
done
