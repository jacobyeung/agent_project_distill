# 9 one-minute checks; prints anomalies at once (and exits), else one summary line
W=/scratch/jjyeung/orch_n30/tree_rebuild27/work/watch.log; DEF='alarm=[] gate=[v.json absent;WAITING_REVIEW.json absent;review.json absent;gate_copy not yet;] hold=no'
for i in $(seq 1 9); do sleep 60
  l=$(grep 'state=' $W | tail -1); t=$(echo "$l" | cut -c1-8); age=$(( $(date +%s) - $(date -d "$t" +%s) ))
  tail -2 $W | grep -q OSSH_FAIL && { echo "ANOM OSSH_FAIL $(tail -1 $W)"; exit 1; }
  echo "$l" | grep -q 'state=RUNNING' || { echo "ANOM state: $l" | cut -c1-400; exit 1; }
  echo "$l" | grep -qF "$DEF" || { echo "ANOM alarm/gate: $(echo "$l" | grep -o 'alarm=.*')"; exit 1; }
  [ $age -gt 200 ] && { echo "ANOM record age ${age}s"; exit 1; }
  pgrep -f "bash wlong3.sh" >/dev/null || { echo "ANOM logger dead"; exit 1; }
done
bash m.sh | head -1 | cut -c1-250; grep '^  q:' $W | tail -1 | cut -c1-160
ls -t /scratch/jjyeung/orch_n30/tree_rebuild27/inbox | head -1
