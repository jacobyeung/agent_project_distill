# usage: p.sh <wait s>: wait, then one rehearsal poll; print stages, errors, gpu, planner, free
sleep ${1:-180}; cd /scratch/jjyeung/orch_n30/tree_rebuild30/work/rh_ext
timeout 120 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < s/o_poll.sh > poll.out 2>&1
head -1 poll.out; sed -n '/== stages/,$p' poll.out | grep -v 'fast path\|srun: error' | cut -c1-400 | head -40
ls -t /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/n_review | head -2
