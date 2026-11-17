# poll general every $2 s up to $1 s; exit when 170956 is gone from squeue (prints squeue)
O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
for i in $(seq 1 $(( $1 / $2 ))); do
  G=$(timeout 120 bash $O 'TZ=UTC squeue -u jjyeung -p general -h -o "%i %j %T %M %R"' 2>&1); echo "$(date -u +%TZ) [$G]" >> /scratch/jjyeung/orch_n30/cont_ops/work/genwait.log
  if [ -n "$G" ] && ! echo "$G" | grep -q '^170956 '; then echo "GONE $(date -u +%TZ) [$G]"; exit 0; fi
  [ -z "$G" ] && { echo "EMPTY $(date -u +%TZ)"; exit 0; }
  sleep $2
done; echo "still $(date -u +%TZ) [$G]"
