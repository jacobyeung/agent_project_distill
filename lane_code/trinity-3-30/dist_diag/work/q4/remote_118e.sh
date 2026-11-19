#!/bin/bash
set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/w16b/work/build16/proofs/census; T=$W/w18/work/tree_r1/student_pilot
echo "== census dir"; ls -la $C $C/* 2>&1 | head -40
nice -n 10 /usr/bin/python3 - <<'PY'
import json, os, glob
C='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16b/work/build16/proofs/census/'
for p in sorted(glob.glob(C+'*.json'))[:6]:
    d=json.load(open(p)); print('== JSON', p, type(d).__name__, (list(d.keys())[:30] if isinstance(d,dict) else len(d)))
    if isinstance(d,dict):
        for k in ('routing','families','cells','eligible','units','absolute_distance','recovery'):
            if k in d: print('  ', k, json.dumps(d[k])[:1500])
I='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16b/work/build16/inputs/'
S=[json.loads(l) for l in open(I+'s.json') if l.strip()]
from collections import Counter
print('== s.json rows', len(S), 'keys', sorted(S[0].keys()), Counter(x.get('family') or x.get('question_type') or x.get('reason') for x in S).most_common(6)); print(json.dumps(S[0])[:300])
M='/scratch/jjyeung/n30_mirror'
for name,p in (('units',M+'/rows_r1/out/vehN_units/repaired/rows_slice.jsonl'),('distance',M+'/rows_r2/out/vehN_pool_abs_distance_full/repaired/rows.jsonl'),('recovery',M+'/rows_r1/out/recovery_v3/rows.jsonl')):
    r=json.loads(open(p).readline())
    print('== ROW', name, 'bytes', len(json.dumps(r)))
    for k,v in r.items():
        s=json.dumps(v); print('  ', k, ':', s[:400])
PY
echo "== ground_rows.py"; cat $T/ground_rows.py
echo "== s1_pool.py validate parts"; grep -n "def \|validate\|unit\|question" $T/s1_pool.py | cut -c1-180 | head -60
echo "== done $(date -u +%FT%TZ)"
