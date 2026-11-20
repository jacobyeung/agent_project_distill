# wait up to $1 s for a new file in events/nvkey or inbox whose name matches regex $2 (or any file naming nv_orch1)
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/nvkey; I=/scratch/jjyeung/orch_n30/nv_orch1/inbox
before=$(ls $E $I | sort -u); end=$(( $(date +%s) + $1 ))
while [ $(date +%s) -lt $end ]; do sleep 30; new=$(comm -13 <(echo "$before") <(ls $E $I | sort -u) | grep -E "$2|nv_orch1|BLOCK" | grep -v "_nv_orch1_" ); [ -n "$new" ] && break; done
date -u +%T; echo "$new"; tail -1 /scratch/jjyeung/orch_n30/nv_orch1/work/watch.log | cut -c1-140
