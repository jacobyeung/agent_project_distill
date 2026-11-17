import json, re, math
P544='/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/0/budget_2048.jsonl'
PD200='/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk/kit/build/a4cadd8934b/fetched/x/main/a0/results/budget_2048/0/items_a0.jsonl'
A544='/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk/evidence/A544.jsonl'
I200='/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk/kit/build/a4cadd8934b/fetched/x/ITEMS.jsonl'
def load(p, types=None):
    out={}
    with open(p) as f:
        for l in f:
            d=json.loads(l)
            qt=d.get('question_type') or d.get('task_type')
            if types and qt not in types: continue
            out[d['id']]=d
    return out
def num(x):
    if x is None: return None
    try: return float(x)
    except: 
        m=re.search(r'-?\d+(?:\.\d+)?', str(x))
        return float(m.group()) if m else None
def mra(p,g):
    if p is None or g is None or g==0: return 0.0
    r=abs(p-g)/abs(g)
    ths=[0.5+0.05*i for i in range(10)]
    return sum(1.0 for c in ths if r < 1-c)/10
UNITS=[('centimet','cm'),('millimet','mm'),('meter','m'),('metre','m'),('inch','in'),('feet','ft'),('foot','ft'),('yard','yd')]
def unit(q):
    ql=q.lower()
    m=re.search(r'\(in ([a-z]+)\)|in ([a-z]+)\s*[\.\?]?\s*$|measured in ([a-z]+)|in ([a-z]+)\b[^a-z]*$', ql)
    for k,u in UNITS:
        if k in ql: return u
    if re.search(r'\bcm\b',ql): return 'cm'
    if re.search(r'\bmm\b',ql): return 'mm'
    if re.search(r'\bm\b',ql): return 'm'
    return '?'
