"""A3, second pass: family-wise false-stop probability and power of R1's harm rule, computed with the
tool's own percentile intervals (room bootstrap, as f1f2.py / room_bootstrap.py).
Noise model: the paired items of D0 m200 against step 544 on dev-S1 (job 170320), seven direct types.
No change: whole rooms are resampled with replacement and, in each drawn room, the two arms are exchanged
with probability 1/2, so every type's true difference is exactly 0 while the observed disagreement between
two checkpoints 200 steps apart is kept.  A loss of L points on a type: each item's score in the later arm
is set to 0 with probability L / (100 x mean score), so the expected loss is L points.
usage: a3_power2.py SEED OUTER INNER"""
import json, sys, math
import numpy as np
R='/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk'
A=[json.loads(l) for l in open(R+'/evidence/A544.jsonl') if l.strip()]
B=[json.loads(l) for l in open(R+'/kit/build/a4cadd8934b/fetched/x/ITEMS.jsonl') if l.strip()]
T=('route_planning','object_counting','object_rel_direction_easy','object_rel_direction_medium',
   'object_rel_direction_hard','object_rel_distance','object_size_estimation')
a={r['id']:r for r in A if r['family']=='main'}; rows=[r for r in B if r['family']=='main' and r['task_type'] in T]
rooms=sorted({r['room'] for r in rows}); ri={x:i for i,x in enumerate(rooms)}; K=len(rooms)
ty=np.array([T.index(r['task_type']) for r in rows]); rm=np.array([ri[r['room']] for r in rows])
sb=np.array([float(r['score']) for r in rows]); sa=np.array([float(a[r['id']]['score']) for r in rows])
room_items=[np.flatnonzero(rm==i) for i in range(K)]; sizes=np.array([len(x) for x in room_items])
pool_mean=np.array([(sa[ty==t].mean()+sb[ty==t].mean())/2 for t in range(7)])
p9=0.095/pool_mean; p2=0.02/pool_mean
SEED,OUT,INN=int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]); rng=np.random.default_rng(SEED)
LEV=np.array([1-0.025/7, 0.975, 1-0.025/28]); MLEV=np.array([0.975, 1-0.025/4])
def counts(k):
    idx=rng.integers(0,k,size=(INN,k)); idx+=np.arange(INN)[:,None]*k
    return np.bincount(idx.ravel(),minlength=INN*k).reshape(INN,k).astype(np.float64)
ub=np.zeros((OUT,3,7,3)); est=np.zeros((OUT,3,7)); se=np.zeros((OUT,3,7)); mub=np.zeros((OUT,9,2)); mest=np.zeros((OUT,9))
for o in range(OUT):
    pick=rng.integers(0,K,size=K); swap=rng.random(K)<0.5
    idx=np.concatenate([room_items[r] for r in pick]); cl=np.repeat(np.arange(K),sizes[pick])
    t=ty[idx]; x=np.where(swap[cl],sb[idx],sa[idx]); y=np.where(swap[cl],sa[idx],sb[idx]); u=rng.random(len(idx))
    key=cl*7+t
    agg=lambda w: np.bincount(key,weights=w,minlength=K*7).reshape(K,7)
    N=agg(np.ones(len(idx))); S=np.stack([agg(y-x), agg(np.where(u<p9[t],0.0,y)-x), agg(np.where(u<p2[t],0.0,y)-x)],0)  # null, loss 9.5 (per type), uniform 2
    for tt in range(7):
        keep=N[:,tt]>0; M=counts(int(keep.sum())); q=(M@S[:,keep,tt].T)/(M@N[keep,tt])[:,None]      # INN x 3 scenarios
        ub[o,:,tt,:]=np.quantile(q,LEV,axis=0).T; se[o,:,tt]=q.std(0); est[o,:,tt]=S[:,:,tt].sum(1)/N[:,tt].sum()
    Mj=counts(K); den=Mj@N; r0=(Mj@S[0])/den; rl=(Mj@S[1])/den; ru=(Mj@S[2])/den
    qs=[r0.mean(1)]+[(r0.sum(1)-r0[:,tt]+rl[:,tt])/7 for tt in range(7)]+[ru.mean(1)]
    mub[o]=np.array([np.quantile(q,MLEV) for q in qs]); e0=est[o,0]
    mest[o]=np.array([e0.mean()]+[(e0.sum()-e0[tt]+est[o,1,tt])/7 for tt in range(7)]+[est[o,2].mean()])
np.savez('pass2_seed%d.npz'%SEED,ub=ub,est=est,se=se,mub=mub,mest=mest,pool_mean=pool_mean,K=K,INN=INN)
print('done',SEED,OUT,INN)
