#!/bin/bash
set -u
T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/tree_r1/student_pilot
echo "== s1_pool.py 60-125"; sed -n 60,125p $T/s1_pool.py
echo "== s1_pool.py 140-200"; sed -n 140,200p $T/s1_pool.py
echo "== s1_routing.py grep pool/events"; grep -n "events\|pool_abs\|absolute_distance\|def \|receipt" $T/s1_routing.py | cut -c1-170 | head -60
/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json
r=json.loads(open('/scratch/jjyeung/n30_mirror/rows_r2/out/vehN_pool_abs_distance_full/repaired/rows.jsonl').readline())
print('== distance row keys', sorted(r.keys()))
print('program_audit keys', sorted((r.get('program_audit') or {}).keys()))
print('provenance keys', sorted((r.get('provenance') or {}).keys()), json.dumps(r.get('provenance'))[:600])
print('suffix', r['suffix'][-400:].replace('\n',' / '))
PY
echo "== done $(date -u +%FT%TZ)"
