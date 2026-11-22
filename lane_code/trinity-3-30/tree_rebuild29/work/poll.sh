# usage: bash poll.sh <wait seconds>; then one rehearsal poll, printed from "== stages"
sleep ${1:-180}; cd /scratch/jjyeung/orch_n30/tree_rebuild29/work/fix15b; o=rd/poll_$(date -u +%H%M).out
timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < s/o_poll.sh > $o 2>&1
head -1 $o; grep -E 'go.log|REFUSE|ERROR|ended|proof' $o | tail -5 | cut -c1-300; sed -n '/== stages/,$p' $o | cut -c1-400
