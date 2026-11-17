"""The R1 harm rule applied to the D0 m200 read itself (dev-S1, against step 544): tool-style percentile intervals."""
import json, numpy as np
R='/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk'
A=[json.loads(l) for l in open(R+'/evidence/A544.jsonl') if l.strip()]
B=[json.loads(l) for l in open(R+'/kit/build/a4cadd8934b/fetched/x/ITEMS.jsonl') if l.strip()]
T=('route_planning','object_counting','object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard','object_rel_distance','object_size_estimation')
a={r['id']:r for r in A if r['family']=='main'}; rows=[r for r in B if r['family']=='main' and r['task_type'] in T]
rooms=sorted({r['room'] for r in rows}); ri={x:i for i,x in enumerate(rooms)}; K=len(rooms)
S=np.zeros((K,7)); N=np.zeros((K,7))
for r in rows:
    t=T.index(r['task_type']); S[ri[r['room']],t]+=r['score']-a[r['id']]['score']; N[ri[r['room']],t]+=1
rng=np.random.default_rng(7); REP=200000; out={}
def counts(k,reps):
    idx=rng.integers(0,k,size=(reps,k)); idx+=np.arange(reps)[:,None]*k
    return np.bincount(idx.ravel(),minlength=reps*k).reshape(reps,k).astype(np.float64)
for t in range(7):
    keep=N[:,t]>0; q=[]
    for _ in range(4):
        M=counts(int(keep.sum()),REP//4); q.append((M@S[keep,t])/(M@N[keep,t]))
    q=100*np.concatenate(q)
    out[T[t]]=dict(delta=round(100*S[:,t].sum()/N[:,t].sum(),2),rooms=int(keep.sum()),se=round(float(q.std()),2),
        ci95=[round(float(v),2) for v in np.quantile(q,[.025,.975])],
        ci_bonf7=[round(float(v),2) for v in np.quantile(q,[0.025/7,1-0.025/7])],
        ci_bonf28=[round(float(v),2) for v in np.quantile(q,[0.025/28,1-0.025/28])])
q=[]
for _ in range(4):
    M=counts(K,REP//4); q.append(((M@S)/(M@N)).mean(1))
q=100*np.concatenate(q)
out['mean_of_seven']=dict(delta=round(float(100*(S.sum(0)/N.sum(0)).mean()),2),rooms=K,se=round(float(q.std()),2),ci95=[round(float(v),2) for v in np.quantile(q,[.025,.975])],ci_98_75=[round(float(v),2) for v in np.quantile(q,[.00625,.99375])])
json.dump(out,open('D0_M200_UNDER_R1_RULE.json','w'),indent=1)
for k,v in out.items(): print(k,json.dumps(v))
