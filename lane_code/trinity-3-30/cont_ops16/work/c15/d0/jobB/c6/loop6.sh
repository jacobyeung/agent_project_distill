#!/bin/bash
# cont_ops6: poll q2.sh every 5 min until metrics_170111.jsonl has 3 complete rows (max 24 polls)
D=/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/c6; T=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools
for i in $(seq 1 24); do
  timeout 300 bash $T/ossh.sh 'bash -s' < $D/q2.sh > $D/q2.tmp 2>&1 && mv $D/q2.tmp $D/q2.out
  sed -n '/== METRICS_BEGIN/,/== METRICS_END/p' $D/q2.out | sed '1d;$d' > $D/metrics_170111.jsonl
  n=$(wc -l < $D/metrics_170111.jsonl); echo "$(date -u +%FT%TZ) poll $i rows $n" >> $D/loop6.log
  [ "$n" -ge 4 ] && break
  sleep 300
done
