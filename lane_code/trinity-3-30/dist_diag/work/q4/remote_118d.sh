#!/bin/bash
# dist_diag coverage rows (read-only): N bound-row membership, row formats, validator code locations.
set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; I=$W/w16b/work/build16/inputs; M=/scratch/jjyeung/n30_mirror
echo "== row_sources.json"; cat $I/row_sources.json | head -c 2100; echo
echo "== CARD.md"; cat $I/CARD.md
nice -n 10 /usr/bin/python3 - <<'PY'
import json
I='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16b/work/build16/inputs/'
m=json.load(open(I+'source_membership.json'))
def sk(d,depth=0,p=''):
    if isinstance(d,dict):
        for k,v in list(d.items())[:12]:
            if isinstance(v,(dict,list)): print(p+str(k)+': '+type(v).__name__+' len %d'%len(v)); sk(v,depth+1,p+'  ') if depth<2 else None
            else: print(p+str(k)+': '+json.dumps(v)[:160])
    elif isinstance(d,list) and d:
        print(p+'[0]: '+json.dumps(d[0])[:200])
print('== source_membership.json'); sk(m)
s=json.load(open(I+'s.json')); print('== s.json'); sk(s)
M='/scratch/jjyeung/n30_mirror'
for name,p in (('units',M+'/rows_r1/out/vehN_units/repaired/rows_slice.jsonl'),('distance',M+'/rows_r2/out/vehN_pool_abs_distance_full/repaired/rows.jsonl'),('recovery',M+'/rows_r1/out/recovery_v3/rows.jsonl')):
    r=json.loads(open(p).readline())
    print('== ROW', name, 'bytes', len(json.dumps(r)))
    for k,v in r.items():
        s=json.dumps(v); print('  ', k, ':', s[:300])
PY
echo "== tree validators"
for T in $W/w18/work/tree_r1 $W/w16b/work/tree_r1; do ls -la $T/student_pilot/ground_rows.py $T/student_pilot/s1_pool.py $T/student_pilot/s1_routing.py 2>&1 | head -4; done
G=$W/w18/work/tree_r1/student_pilot/ground_rows.py
[ -f $G ] && grep -n "^def \|unit\|question\|raise ValueError" $G | cut -c1-200 | head -60
echo "== done $(date -u +%FT%TZ)"
