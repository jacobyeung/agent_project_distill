cd /scratch/jjyeung/orch_n30/tree_rebuild26/work; end=$(( $(date +%s) + 570 ))
while [ $(date +%s) -lt $end ]; do timeout 120 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < o13.sh >> pend.log 2>&1; tail -1 pend.log | grep -q RUNNING && break; sleep 120; done; tail -3 pend.log
