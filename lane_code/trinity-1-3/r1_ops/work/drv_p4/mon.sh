#!/bin/bash
D=/scratch/jjyeung/orch_n30/r1_ops/work/drv_p4; OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
cd $D; fail=0
for gap in 60 60 60 120 120 300 300 600 600 600 600 600 600 600 600 600 600 600 600 600 600 600 600 600 600 600 600 600 600; do
  { echo "=== $(date -u +%FT%TZ)"; cat yieldchk.sh pm1.sh | timeout 150 bash $OSSH 'bash -s' 2>&1 | grep -v '| joined\|archive .* staged' | tail -25; } > mon_last.txt; rc=$?
  cat mon_last.txt >> mon_hist.txt
  if grep -q 'SCANCELLED' mon_last.txt; then echo YIELDED > mon_flag; exit 0; fi
  if grep -q '"status": "\(PASS\|FAIL\)"' mon_last.txt; then echo DONE > mon_flag; exit 0; fi
  if ! grep -q '170956' mon_last.txt; then fail=$((fail+1)); else fail=0; fi
  [[ $fail -ge 2 ]] && { echo NOJOB > mon_flag; exit 0; }
  sleep $gap
done
