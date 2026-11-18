#!/bin/bash
# r1_ops6 monitor: one Orchard call (drv_cp/mon.sh) per interval (work/mon/sleep, default 60 s); stop with work/mon/stop.
M=/scratch/jjyeung/orch_n30/r1_ops6/work/mon; D=/scratch/jjyeung/orch_n30/r1_ops6/rec/r1_ops/work/drv_cp
while [[ ! -e $M/stop ]]; do
  { date -u +%FT%TZ; timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < $D/mon.sh 2>&1 | grep -v -E "^@|WARNING: REMOTE|POSSIBLE|eavesdropping|host key|fingerprint|SHA256:lXw|contact your|google_compute_known|Offending|authentication is disabled"; } > $M/last.tmp
  mv $M/last.tmp $M/last.txt; { echo "=== $(head -1 $M/last.txt)"; sed -n 2,3p $M/last.txt; } >> $M/hist.txt
  sleep $(cat $M/sleep 2>/dev/null || echo 60)
done
