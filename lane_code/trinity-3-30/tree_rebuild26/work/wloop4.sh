cd /scratch/jjyeung/orch_n30/tree_rebuild26/work; end=$(( $(date +%s) + ${1:-540} )); itv=${2:-60}; last=""; same=0
while [ $(date +%s) -lt $end ]; do timeout 90 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < w1.sh >> watch.log 2>&1 || echo "$(date -u +%TZ) OSSH_FAIL" >> watch.log
 l=$(grep 'state=' watch.log | tail -1); n=$(echo "$l" | grep -o ' n=[0-9]*'); q=$(echo "$l" | grep -o 'tq=[0-9]*')
 if [ "$n$q" = "$last" ]; then same=$((same+1)); else same=0; last="$n$q"; fi
 [ $same -ge 3 ] && echo "$(date -u +%TZ) STALL live n and t_q.log unchanged for 3 reads" >> watch.log
 tail -4 watch.log | grep -q 'state=GONE\|MEM_ALARM\|OOM_EVENT\|OSSH_FAIL\|STALL\|WAITING_REVIEW.json bytes' && break; sleep $itv; done; tail -6 watch.log | cut -c1-400
