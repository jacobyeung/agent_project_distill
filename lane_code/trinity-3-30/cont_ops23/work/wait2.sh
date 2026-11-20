# wait up to 580 s for: job leaving queue, new ORCH event, inbox file
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops
L=/scratch/jjyeung/orch_n30/cont_ops21/work/monG_173412.log
n0=$(ls $E | grep -c _ORCH_); i0=$(ls /scratch/jjyeung/orch_n30/cont_ops23/inbox | wc -l)
for k in $(seq 1 29); do
  [ $(ls $E | grep -c _ORCH_) != $n0 ] && break
  [ $(ls /scratch/jjyeung/orch_n30/cont_ops23/inbox | wc -l) != $i0 ] && break
  sleep 20
done
date -u +%TZ; tail -1 $L; ls -t $E | grep _ORCH_ | head -2; ls /scratch/jjyeung/orch_n30/cont_ops23/inbox
