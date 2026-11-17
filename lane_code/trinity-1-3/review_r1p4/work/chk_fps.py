import json,gzip,random,math
K='/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/'
r=json.load(open(K+'frame_rates.json'));plan=json.load(gzip.open(K+'frame_plan.json.gz','rt'))
ds={}
for k,v in r['by_scene'].items(): ds.setdefault(k.split('/')[0],set()).add(v)
print({k:sorted(v) for k,v in ds.items()}, list(plan)[:5])
pk=[json.loads(l) for l in open('/scratch/jjyeung/orch_n30/review_r1p4/work/f8/out/units/packed.jsonl')]
bad=0;src=dict(scene=0,uniform=0);lb=0
for p in pk:
    d,s=p['provenance']['alias'].split('/',1);si=p['student_input']
    e=r['by_scene'].get(d+'/'+s)
    if e is None:
        assert len(ds[d])==1;e=next(iter(ds[d]));src['uniform']+=1
    else: src['scene']+=1
    v=plan['v'].get(s)
    tot=max(si['frame_indices'])+1 if (v is None or v.get('raw_n') is None) else v['raw_n']
    if v is None or v.get('raw_n') is None: lb+=1; assert d=='d3'
    else: assert v['g']==d
    ts=[i/e for i in si['frame_indices']]
    ok= si['fps']==e and si['total_num_frames']==tot and all(math.isclose(a,b,abs_tol=1e-12) for a,b in zip(si['timestamps'],ts)) and si['question']==p['question'] and si['options']==(p['options'] or [])
    bad+= not ok
print(dict(bad=bad,**src,lower_bound=lb))
