F=/scratch/jjyeung/orch_n30/tree_rebuild29/work/fix22; OS=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
for i in $(seq 1 40); do
  echo "=== poll $i $(date -u +%TZ)" >> $F/s/poll.log; echo "call $(date -u +%FT%TZ) poll 174369" >> $F/s/CALLS.log
  timeout 120 bash $OS 'bash -s' < $F/s/o_poll_174369.sh > $F/s/poll_last.out 2>&1; cat $F/s/poll_last.out >> $F/s/poll.log
  grep -qE "^(COMPLETED|FAILED|CANCELLED|TIMEOUT|PREEMPTED|OUT_OF_ME|NODE_FAIL)" <(grep -A1 -m1 "JOBID" $F/s/poll_last.out >/dev/null; awk '{print $1}' $F/s/poll_last.out) && { echo ENDED >> $F/s/poll.log; exit 0; }
  sleep 180
done
