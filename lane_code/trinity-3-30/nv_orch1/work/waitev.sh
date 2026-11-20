# wait up to $1 seconds for a new event/inbox file; print new names
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/nvkey; I=/scratch/jjyeung/orch_n30/nv_orch1/inbox
a=$(ls $E $I | sort | md5sum); end=$(( $(date +%s) + $1 ))
while [ $(date +%s) -lt $end ]; do sleep 30; b=$(ls $E $I | sort | md5sum); [ "$a" != "$b" ] && break; done
date -u +%T; ls -t $E | grep -E "^2026" | head -3; ls -t $I | head -2; tail -1 /scratch/jjyeung/orch_n30/nv_orch1/work/watch.log | cut -c1-160
