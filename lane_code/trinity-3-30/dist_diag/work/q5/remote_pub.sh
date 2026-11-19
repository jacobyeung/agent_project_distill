#!/bin/bash
set -u
O=/scratch/jjyeung/n30_mirror/dist_diag/coverage_v1; G=/scratch/jjyeung/n30_mirror/dist_diag/gen
D=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/dist_diag
cd /scratch/jjyeung/n30_mirror/dist_diag && cp $G/coverage_rows.py $G/recovery_check.py $G/TEMPLATES_V1.json $O/ && \
tar cf COVERAGE_V1_PUB.tar -C $O COVERAGE_UNITS_V1.jsonl.gz COVERAGE_DISTANCE_V1.jsonl.gz SUMMARY.json READ30.txt RECOVERY_CHECK.json coverage_rows.py recovery_check.py TEMPLATES_V1.json && \
ls -la COVERAGE_V1_PUB.tar && sha256sum COVERAGE_V1_PUB.tar && \
nice -n 10 cp COVERAGE_V1_PUB.tar $D/COVERAGE_V1_PUB.tar && sha256sum $D/COVERAGE_V1_PUB.tar
echo "== SUMMARY"; cat $O/SUMMARY.json | head -c 3600; echo
echo "== READ30 tails"; /scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import re
t=open('/scratch/jjyeung/n30_mirror/dist_diag/coverage_v1/READ30.txt').read().split('\n')
for i in range(0,len(t)-2,3):
    if not t[i].strip(): continue
    q=t[i+1].strip(); body=t[i+2]
    tail=body.split('The box gap is the smallest distance between points on a grid over both objects\' full boxes, taken over every pair of instances. / ')[-1]
    print(t[i].strip(), '|', q[3:], '||', tail[:160])
PY
echo "== done $(date -u +%FT%TZ)"
