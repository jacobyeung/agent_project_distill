"""card_fix2, B3/B5/B6: step 544's own-arm distance read (job 170706, items.jsonl 826385c6, unperturbed reads).
1. Exact unit baseline: correct conversions over ALL non-metre items (rule of card_fix/out/unit_none.py: the read answers
   with a served gap value and the answer equals the printed metres times the question's unit factor within 5%).
2. Minimum detectable improvement of the unit gate (95% room-bootstrap interval of the paired difference wholly above
   zero) and of the recovery gate on the reads that drew a status, from this read's paired room distribution.
   Later arm: an item wrong at step 544 turns right with probability q, an item right turns wrong with probability r.
These are own-arm planning values; the registered baseline is the tower-arm read with the pinned selector (B4).
usage: b5_units.py SEED OUTER INNER"""
import json, re, sys, math, collections
import numpy as np
F='/scratch/jjyeung/orch_n30/reader_r1/work/b1p/in/h10own/170706/items.jsonl'
M=json.load(open('/scratch/jjyeung/orch_n30/cont_ops/work/h1eval_repin/out/production/items/devs1_routed.json')); by={r['id']:r for r in M['items']}
FAC={'centimet':100,'inch':1/0.0254,'feet':1/0.3048,'foot':1/0.3048,'meter':1,'metre':1}
SEED,OUT,INN=int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]); rng=np.random.default_rng(SEED)
def st(x):
    r=(x.get('response') or '')
    if not x['served']: return 'unserved'
    if 'not seen' in r: return 'not_seen'
    if r.startswith('error'): return 'error'
    return 'ok'
per={}
for x in map(json.loads,open(F)):
    if x['mode']!='none': continue
    q=by[x['id']]['question'].lower(); unit=next((w for w in FAC if w in q),'?'); f=FAC.get(unit)
    cap=x['output']['finish']=='max_calls'
    ns=any(st(c)=='not_seen' for c in x['output']['calls']['records'])
    if cap: k='capped'
    else:
        g=[c2['printed']['distance'] for c2 in x['measurements']['M2']['calls'] if c2.get('printed')]
        m=re.findall(r'<answer>\s*(.*?)\s*</answer>',x['output']['text'],re.S)
        try: a=float(re.match(r'\s*([-\d.]+)',m[-1])[1])
        except Exception: a=None
        if a is None: k='noparse'
        elif not g: k='no_gap_value'
        else:
            d=g[-1]; near=lambda v: abs(a-v)<=0.05*abs(v)+1e-9
            k='metres_unconverted' if near(d) and f!=1 else 'converted' if near(d*f) else 'other'
    per[x['id']]=dict(unit=unit,room=by[x['id']]['room'],cls=k,capped=cap,status=ns,score=float(x['measurements']['M2']['task_accuracy']))
nm=[v for v in per.values() if v['unit'] not in ('meter','metre')]
out=dict(source=F,reads=len(per),rooms_all=len({v['room'] for v in per.values()}),
         units=dict(collections.Counter(v['unit'] for v in per.values())),
         classes_non_metre=dict(collections.Counter(v['cls'] for v in nm)),
         classes_non_metre_by_unit={u:dict(collections.Counter(v['cls'] for v in nm if v['unit']==u)) for u in sorted({v['unit'] for v in nm})},
         non_metre_items=len(nm),non_metre_rooms=len({v['room'] for v in nm}),converted=sum(v['cls']=='converted' for v in nm),
         answered_with_gap_value=sum(v['cls'] in ('converted','metres_unconverted','other') for v in nm),
         capped_all=sum(v['capped'] for v in per.values()),status_all=sum(v['status'] for v in per.values()),
         capped_among_status=sum(v['capped'] and v['status'] for v in per.values()),
         mra_status=round(float(np.mean([v['score'] for v in per.values() if v['status']])),4))
def counts(k):
    idx=rng.integers(0,k,size=(INN,k)); idx+=np.arange(INN)[:,None]*k
    return np.bincount(idx.ravel(),minlength=INN*k).reshape(INN,k).astype(np.float64)
def mdi(items,good,r_back,GRID):
    rooms=sorted({v['room'] for v in items}); ri={x:i for i,x in enumerate(rooms)}; K=len(rooms)
    rm=np.array([ri[v['room']] for v in items]); sa=np.array([float(good(v)) for v in items]); p0=float(sa.mean())
    room_items=[np.flatnonzero(rm==i) for i in range(K)]; sizes=np.array([len(x) for x in room_items])
    Q=[(g/100+r_back*p0)/(1-p0) for g in GRID]; lb=np.zeros((OUT,len(GRID)))
    for o in range(OUT):
        pick=rng.integers(0,K,size=K); idx=np.concatenate([room_items[r] for r in pick]); cl=np.repeat(np.arange(K),sizes[pick])
        x=sa[idx]; u=rng.random(len(idx)); v=rng.random(len(idx))
        D=np.stack([np.where(x<1,(u<q).astype(float),np.where(v<r_back,0.0,1.0))-x for q in Q],0)
        S=np.stack([np.bincount(cl,weights=d,minlength=K) for d in D],0); N=np.bincount(cl,minlength=K).astype(float)
        Mx=counts(K); lb[o]=np.quantile((Mx@S.T)/(Mx@N)[:,None],0.025,axis=0)
    pw=[float((lb[:,j]>0).mean()) for j in range(len(GRID))]
    def cross(level):
        for j in range(1,len(GRID)):
            if pw[j-1]<level<=pw[j]: return round(GRID[j-1]+(GRID[j]-GRID[j-1])*(level-pw[j-1])/(pw[j]-pw[j-1]),2)
        return None
    return dict(items=len(items),rooms=K,baseline_right=int(sa.sum()),back_flip_rate=r_back,grid_pp=GRID,power=[round(p,4) for p in pw],
                mdi50_pp=cross(0.5),mdi80_pp=cross(0.8),mdi80_items=None if cross(0.8) is None else round(cross(0.8)*len(items)/100,1))
G=[1.0,2,3,4,5,6,8,10,12,15,20]
out['unit_gate_no_back_flips']=mdi(nm,lambda v:v['cls']=='converted',0.0,G)
out['unit_gate_back_flips_0.156']=mdi(nm,lambda v:v['cls']=='converted',0.15625,G)
stt=[v for v in per.values() if v['status']]
out['recovery_gate_terminating_reads_no_back_flips']=mdi(stt,lambda v:not v['capped'],0.0,G+[25.0,30.0])
out['recovery_gate_terminating_reads_back_flips_0.156']=mdi(stt,lambda v:not v['capped'],0.15625,G+[25.0,30.0])
json.dump(dict(out,per_item=per),open('B5_UNITS_RECOVERY_OWN_ARM.json','w'),indent=0)
print(json.dumps(out,indent=1))
