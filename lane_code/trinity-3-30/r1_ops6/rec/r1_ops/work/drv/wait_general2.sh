#!/bin/bash
# one ossh squeue per 5 min; when general has no a15_cot_ap* and no jjy_* job, run pr2.sh once
D=/scratch/jjyeung/orch_n30/r1_ops/work/drv; OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
cd $D
fail=0
for i in $(seq 1 60); do
  out=$(timeout 120 bash $OSSH 'TZ=UTC squeue -u $USER -h -p general -o "%i|%j|%T|%M"' 2>&1); rc=$?
  echo "$(date -u +%FT%TZ) rc=$rc [$out]" >> wait_general.log
  if [[ $rc -eq 0 && -z "$(echo "$out" | grep -E 'a15_cot_ap|jjy_')" ]]; then
     timeout 300 bash $OSSH 'bash -s' < pr2.sh > pr2.out 2>&1; echo "$(date -u +%FT%TZ) pr2 rc=$?" >> wait_general.log; exit 0
  fi
  if [[ $rc -ne 0 ]]; then fail=$((fail+1)); [[ $fail -ge 2 ]] && { echo "$(date -u +%FT%TZ) two ossh failures: BLOCKER, exit" >> wait_general.log; exit 3; }; sleep 120; else fail=0; sleep 300; fi
done
