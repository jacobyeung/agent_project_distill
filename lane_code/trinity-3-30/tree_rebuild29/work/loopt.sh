# training-phase watch: N one-minute checks; prints each change of the live t.log tail (kt line); exits 1 on anomaly
W=/scratch/jjyeung/orch_n30/tree_rebuild28/work/watch.log; last=$(grep '^  kt:' $W | tail -1)
for i in $(seq 1 ${1:-9}); do sleep 60
  l=$(grep 'state=' $W | tail -1); t=$(echo "$l" | cut -c1-8); age=$(( ( $(date +%s) - $(TZ=UTC date -d "$t" +%s) + 172800 ) % 86400 ))
  tail -4 $W | grep -q OSSH_FAIL && { echo "ANOM OSSH_FAIL $(tail -1 $W)"; exit 1; }
  echo "$l" | grep -q 'state=RUNNING' || { echo "ANOM state: $l" | cut -c1-400; exit 1; }
  echo "$l" | grep -qF "alarm=[] " || { echo "ANOM alarm: $(echo "$l" | grep -o 'alarm=.*' | cut -c1-300)"; exit 1; }
  [ $age -gt 200 ] && { echo "ANOM record age ${age}s"; exit 1; }
  pgrep -f "bash wlong4.sh" >/dev/null || { echo "ANOM logger dead"; exit 1; }
  k=$(grep '^  kt:' $W | tail -1); [ "$k" != "$last" ] && { echo "$t CHANGE$k" | cut -c1-700; last=$k; }
done
bash m.sh | head -1 | cut -c1-220; grep -m1 "Job 174246" /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/n_ops/N_WATCH_STATUS.md | cut -c1-220
