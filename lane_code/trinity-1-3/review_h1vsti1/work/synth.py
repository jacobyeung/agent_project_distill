import json, random, hashlib, collections, subprocess, sys
import numpy as np
K='/scratch/jjyeung/orch_n30/cont_ops/work/h1vsti/'
W='/scratch/jjyeung/orch_n30/review_h1vsti1/work/synth/'
ast=[json.loads(l) for l in open(K+'assets/b62c14e9.jsonl')]
mp=json.load(open(K+'evidence/R6_ID_MAP.json'))
P={'cur':0.70,'base':0.55}
# type-specific: make ud strongly worse in cur
def make(name, cfgdir, step, decode):
    import os
    root=W+name+'/fetched/x/'; os.makedirs(root+'r6',exist_ok=True)
    spec=json.load(open(K+'kit/build/'+cfgdir+'/CONFIG.json'))['spec']
    json.dump(spec,open(root+'SPEC.json','w')); json.dump(dict(complete=True),open(root+'SUMMARY.json','w'))
    rng=random.Random(name); rows=[]
    for a in ast:
        p=P[name]
        if name=='cur' and a['question_type'].endswith('_ud'): p=0.20
        s=int(rng.random()<p); n=len(a['options'])
        pred=a['answer'] if s else rng.choice([x for x in 'ABCD'[:n] if x!=a['answer']]+[None])
        r=dict(id=a['id'],family='r6',room=a['room'],scene=a['scene'],task_type=a['question_type'],prediction=pred,predicted_letter=pred,gold_letter=a['answer'],score=s,budget=2048,step=step,scoring_basis='answer',template_capture=rng.random()<0.1,trace_sha256='0'*64)
        if decode: r=dict(r,**mp[a['id']])
        rows.append(r)
    open(root+'r6/ITEMS.jsonl','w').write(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
    return rows
base=make('base','acb2faedd41',544,False); cur=make('cur','a35f73e87f0',200,True)
# independent expectation
phys={a['id']:mp[a['id']]['room'] for a in ast}
bid={r['id']:r for r in base}; cid={mp[a]['id']:a for a in mp}
def exp(filt):
    d=collections.defaultdict(list)
    for r in cur:
        op=cid[r['id']]; b=bid[op]
        if filt(r): d[phys[op]].append(r['score']-b['score'])
    rooms=sorted(d); S=np.array([sum(d[k]) for k in rooms]); N=np.array([len(d[k]) for k in rooms])
    g=np.random.default_rng(1); idx=g.integers(0,len(rooms),(20000,len(rooms)))
    bs=S[idx].sum(1)/N[idx].sum(1)
    acc=100*np.mean([r['score'] for r in cur if filt(r)])
    return dict(acc=acc,delta=100*S.sum()/N.sum(),ci=list(100*np.percentile(bs,[2.5,97.5])),rooms=len(rooms))
types=sorted({a['question_type'] for a in ast})
E={t:exp(lambda r,t=t:r['task_type']==t) for t in types}; E['pooled']=exp(lambda r:True)
out=json.loads(subprocess.run([sys.executable,'-B',K+'vsti_summary.py','--read',W+'cur/fetched/x','--base',W+'base/fetched/x','--json'],capture_output=True,text=True,check=True).stdout)
for t in types+['pooled']:
    o=out['per_type'][t] if t!='pooled' else out['pooled']
    print(t, 'acc %.3f/%.3f'%(o['accuracy_pct'],E[t]['acc']), 'd %.3f/%.3f'%(o['paired']['delta_pp'],E[t]['delta']), 'ci', [round(x,2) for x in o['paired']['ci95_pp']], [round(x,2) for x in E[t]['ci']], 'rooms',o['paired']['rooms'],E[t]['rooms'], o['paired']['seed'],o['paired']['replicates'], 'below',o['paired']['wholly_below_zero'])
print('gate',out['gate'])
print('capture pooled', out['pooled']['template_capture_pct'], 100*np.mean([r['template_capture'] for r in cur]))
print(subprocess.run([sys.executable,'-B',K+'vsti_summary.py','--read',W+'base/fetched/x'],capture_output=True,text=True).stdout)
