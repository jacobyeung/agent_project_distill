# Detached 1-minute watch log of the launch job (no events; read work/watch.log). Usage: nohup bash wlong.sh <seconds> &
cd /scratch/jjyeung/orch_n30/tree_rebuild27/work; end=$(( $(date +%s) + ${1:-10800} ))
while [ $(date +%s) -lt $end ]; do timeout 90 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < w3.sh >> watch.log 2>&1 || echo "$(date -u +%TZ) OSSH_FAIL" >> watch.log; grep -q 'state=GONE' <(tail -3 watch.log) && break; sleep 60; done
