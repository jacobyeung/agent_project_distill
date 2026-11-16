# wait until watcher ends or a new ORCH event/inbox file appears, max $1 seconds
EV=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/native_r4
O=/scratch/jjyeung/orch_n30/native_r4/work/orchard
n0=$(ls $EV | grep -c _ORCH_); i0=$(ls /scratch/jjyeung/orch_n30/native_r4/inbox | wc -l); end=$(( $(date +%s) + $1 ))
while [ $(date +%s) -lt $end ]; do
  grep -qE "^(SUBMITTED|CUTOFF|UNEXPECTED)" $O/watch3.log && break
  [ $(ls $EV | grep -c _ORCH_) -ne $n0 ] && break
  [ $(ls /scratch/jjyeung/orch_n30/native_r4/inbox | wc -l) -ne $i0 ] && break
  sleep 60
done
date -u +%T; tail -3 $O/watch3.log; ls -t $EV | grep _ORCH_ | head -2
