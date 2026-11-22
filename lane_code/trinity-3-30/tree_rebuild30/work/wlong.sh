# Detached watch log of N job (no events; read work/watch.log). Record = 5 lines (state + q,j2,kq,kt); stop check reads tail -5. Cadence from work/wsleep (s, default 60).
cd /scratch/jjyeung/orch_n30/tree_rebuild30/work; end=$(( $(date +%s) + ${1:-36000} ))
while [ $(date +%s) -lt $end ]; do timeout 90 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < w3.sh >> watch.log 2>&1 || echo "$(date -u +%TZ) OSSH_FAIL" >> watch.log; grep -q 'state=GONE' <(tail -5 watch.log) && break; s=$(cat wsleep 2>/dev/null); sleep ${s:-60}; done
