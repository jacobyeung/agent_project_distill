# local babysit loop: poll 1-13 every 10 min; exit early on any new ORCH file, new main inbox, or chain/EXIT event
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/b04_e2ehook
O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918
W=/scratch/jjyeung/orch_n30/b04_e2ehook/work/s4
n0=$(ls $E | wc -l); i0=$(ls -t $O/INBOX_TO_DISTILL_ORCH_* | head -1); b0=$(ls /scratch/jjyeung/orch_n30/b04_e2ehook/inbox | wc -l)
for k in $(seq 1 ${1:-6}); do
  sleep 590
  out=$(bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/tssh.sh trinity-1-13 'bash -s' < $W/cpoll.sh 2>&1)
  echo "$(date -u +%H:%MZ) $out" >> $W/poll.log
  echo "$out" | grep -q "EXIT\|CHAIN\|rror\|raceback" && { echo "EVENT"; echo "$out"; exit; }
  [ "$(ls $E | wc -l)" != "$n0" ] && { echo "NEW_EVENTS"; ls -t $E | head -3; echo "$out"; exit; }
  [ "$(ls -t $O/INBOX_TO_DISTILL_ORCH_* | head -1)" != "$i0" ] && { echo "NEW_INBOX $(ls -t $O/INBOX_TO_DISTILL_ORCH_* | head -1)"; echo "$out"; exit; }
  [ "$(ls /scratch/jjyeung/orch_n30/b04_e2ehook/inbox | wc -l)" != "$b0" ] && { echo "NEW_LANE_INBOX"; echo "$out"; exit; }
done
echo "ROUTINE"; echo "$out"
