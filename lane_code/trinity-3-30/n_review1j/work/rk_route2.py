import sys,json,sqlite3,os,collections
N='/tmp/q_22c714e1_174134'; DBG='/tmp/a15_dbg_174134'
import glob
sys.path.insert(0,N+'/p/s'); sys.path.insert(1,N+'/s/np226'); sys.path.extend(glob.glob(N+'/s/c7d31ddd/venvs/rwtrain_torch211_cu129/lib/python3*/site-packages'))
import student_pilot.r1_persisted as rp
_orig=rp.relocated
def reloc(pin):
    try:
        p=str(_orig(pin))
        if os.path.isfile(p): return p
    except Exception: pass
    p=pin['path']; sha=pin['sha256']
    for c in (p.replace('/tmp/q_22c714e1/',N+'/',1), N+'/p/q/u/'+sha, N+'/u/'+sha, p):
        if os.path.isfile(c): return c
    return p
rp.relocated=reloc
from student_pilot.r2_scene_bindings import rows
from student_pilot.s1_exclusions import Exclusions
from student_pilot.s1_exclusions import Exclusions
from student_pilot.p3_provenance import pinned, load
from collections import Counter
Q=N+'/p/q'; c=json.load(open(Q+'/c.json'))
rule=Exclusions(c['dev_scene_exclusions'], c['benchmark_scene_exclusions'])
sc0=json.load(open(Q+'/sc/0/0.json'))
cnt=Counter(); first=None
for i,r in enumerate(rows(sc0['scene_rebuild']['population'])):
    if first is None: first=r; print('base row keys',sorted(r)[:40]); print('routing',json.dumps(r.get('routing'))[:300])
    if any(rule.matches(r).values()):
        rt=r.get('routing') or {}
        cnt[(rt.get('question_type') or rt.get('type') or r.get('category'), r.get('head_layout') or rt.get('head_layout'))]+=1
print(cnt.most_common(12))
