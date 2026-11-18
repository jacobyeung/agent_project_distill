#!/bin/bash
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1orch
timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < m3.sh > m3.out 2>&1; echo "rc=$?"; cat m3.out >> m1_hist.txt; cat m3.out
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops; ls -t $E | grep _ORCH_ | head -2; ls -t /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918 | grep INBOX_TO_DISTILL | head -1
