import json, sys, importlib.util, numpy as np, collections
spec=importlib.util.spec_from_file_location('nvd','out/native_vs_direct.py'); N=importlib.util.module_from_spec(spec); spec.loader.exec_module(N)
rows=[json.loads(l) for f in ('main','camera') for l in open(f'in/direct_raw/items_leg_m544_{f}.jsonl')]
out={}
for qt in ('object_abs_distance','room_size_estimation','camera_displacement'):
    R=[r for r in rows if r['question_type']==qt]
    # cell: "native" stand-in = direct capped_zeroed score, "scripted" = direct with producer errors... direct = recorded score
    cell=[(r['room'], N.capped_score(r,True), float(r['score']>0), r['score']) for r in R]
    s=N.bootstrap(cell,50000,20261115)
    # independent numpy bootstrap, different RNG
    rooms=sorted({c[0] for c in cell}); idx={r:i for i,r in enumerate(rooms)}
    n=np.zeros(len(rooms)); d=np.zeros((2,len(rooms)))
    for c in cell:
        i=idx[c[0]]; n[i]+=1; d[0,i]+=c[1]-c[3]; d[1,i]+=c[2]-c[3]
    rng=np.random.default_rng(7); draws=rng.integers(0,len(rooms),size=(200000,len(rooms)))
    den=n[draws].sum(1)
    ind=[list(np.percentile(100*d[j][draws].sum(1)/den,[2.5,97.5])) for j in (0,1)]
    pt=[100*d[j].sum()/n.sum() for j in (0,1)]
    out[qt]=dict(items=len(cell),rooms=len(rooms),point=pt,script=s,indep=ind,
                 direct_primary_pct=100*np.mean([c[3] for c in cell]),direct_capped_pct=100*np.mean([c[1] for c in cell]))
print(json.dumps(out,indent=1))
