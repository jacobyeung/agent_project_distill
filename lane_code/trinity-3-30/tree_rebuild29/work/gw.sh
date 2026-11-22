# wait up to N min for a new n_review or n_ops event or inbox file; exits on it or on an anomaly
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; W=/scratch/jjyeung/orch_n30/tree_rebuild28/work/watch.log
a=$(ls $B/events/n_review $B/events/n_ops $B/events/tree_rebuild /scratch/jjyeung/orch_n30/tree_rebuild29/inbox | sort | md5sum)
for i in $(seq 1 ${1:-9}); do sleep 60
  l=$(grep 'state=' $W | tail -1)
  echo "$l" | grep -q 'state=RUNNING' || { echo "ANOM state: $l" | cut -c1-400; exit 1; }
  echo "$l" | grep -qF "alarm=[] " || { echo "ANOM alarm: $(echo "$l" | grep -o 'alarm=.*')"; exit 1; }
  echo "$l" | grep -qF "hold=no" || { echo "ANOM hold"; exit 1; }
  echo "$l" | grep -qF "review.json absent" || { echo "REVIEW: $(echo "$l" | grep -o 'gate=.*')"; exit 2; }
  b=$(ls $B/events/n_review $B/events/n_ops $B/events/tree_rebuild /scratch/jjyeung/orch_n30/tree_rebuild29/inbox | sort | md5sum)
  [ "$a" != "$b" ] && { echo "NEW at $(date -u +%TZ):"; ls -t $B/events/n_review | head -2; ls -t $B/events/n_ops | head -2; ls -t $B/events/tree_rebuild | head -3; ls -t /scratch/jjyeung/orch_n30/tree_rebuild29/inbox | head -2; exit 3; }
done; echo "nothing new $(date -u +%TZ); $(echo "$l" | grep -o 'gate waiting_since[^;]*')"
