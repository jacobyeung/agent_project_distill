"""card_fix2, amendments B2/B5/B8 and ORCH NOTE 1523Z: conditional simulation estimates for R1 card v3.
Inputs (read-only): step-544 arm evidence/A544.jsonl and D0 m200 ITEMS.jsonl of the read kit (job 170320),
the same paired files lane card_fix used (card_fix/work/a3).  Double bootstrap as a3_power2.py: the outer loop
draws pseudo-reads by resampling whole physical rooms, the inner loop computes the tool's percentile interval.
modes:
  harm NAME  : outcome NAME under the harm rule's levels.  No change: arms exchanged per drawn room with
               probability 1/2.  Loss L: later-arm item score set to 0 with probability L/(100 x mean score).
  gate NAME  : efficacy gate (95% interval wholly above zero) on NAME against step 544.  Later arm: an item
               wrong at step 544 turns right with probability q; an item right turns wrong with probability r.
usage: b5_sim.py MODE NAME SEED OUTER INNER"""
import json, sys, math
import numpy as np
R='/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk'
A=[json.loads(l) for l in open(R+'/evidence/A544.jsonl') if l.strip()]
B=[json.loads(l) for l in open(R+'/kit/build/a4cadd8934b/fetched/x/ITEMS.jsonl') if l.strip()]
SETS=dict(size=('main','object_size_estimation'),relsize=('main','relative_size_object'),toward=('forward',None),away=('away',None))
MODE,NAME,SEED,OUT,INN=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5])
fam,tt=SETS[NAME]
a=[r for r in A if r['family']==fam and (tt is None or r['task_type']==tt)]
b={r['id']:r for r in B if r['family']==fam}
rooms=sorted({r['room'] for r in a}); ri={x:i for i,x in enumerate(rooms)}; K=len(rooms)
rm=np.array([ri[r['room']] for r in a]); sa=np.array([float(r['score']) for r in a]); sb=np.array([float(b[r['id']]['score']) for r in a])
assert all(b[r['id']]['room']==r['room'] for r in a)
room_items=[np.flatnonzero(rm==i) for i in range(K)]; sizes=np.array([len(x) for x in room_items])
rng=np.random.default_rng(SEED)
def counts(k):
    idx=rng.integers(0,k,size=(INN,k)); idx+=np.arange(INN)[:,None]*k
    return np.bincount(idx.ravel(),minlength=INN*k).reshape(INN,k).astype(np.float64)
def rate(x):
    p=float(np.mean(x)); return [round(p,4), round(math.sqrt(max(p*(1-p),1e-12)/len(x)),4)]
out=dict(mode=MODE,name=NAME,items=len(a),rooms=K,seed=SEED,outer=OUT,inner=INN,
         step544_mean=round(float(sa.mean()),4),d0m200_mean=round(float(sb.mean()),4),
         right_to_wrong=int(((sa>=1)&(sb<1)).sum()) if set(np.unique(sa))<={0.0,1.0} else None,
         wrong_to_right=int(((sa<1)&(sb>=1)).sum()) if set(np.unique(sa))<={0.0,1.0} else None)
if MODE=='harm':
    pool=(sa.mean()+sb.mean())/2; LOSS=[float(v) for v in sys.argv[6].split(',')]
    LEV=np.array([1-0.025/7, 1-0.025/28, 0.975])     # upper quantile: step 200, later looks, plain 95%
    ub=np.zeros((OUT,1+len(LOSS),3)); est=np.zeros((OUT,1+len(LOSS)))
    for o in range(OUT):
        pick=rng.integers(0,K,size=K); swap=rng.random(K)<0.5
        idx=np.concatenate([room_items[r] for r in pick]); cl=np.repeat(np.arange(K),sizes[pick])
        x=np.where(swap[cl],sb[idx],sa[idx]); y=np.where(swap[cl],sa[idx],sb[idx]); u=rng.random(len(idx))
        D=np.stack([y-x]+[np.where(u<L/(100*pool),0.0,y)-x for L in LOSS],0)
        S=np.stack([np.bincount(cl,weights=d,minlength=K) for d in D],0); N=np.bincount(cl,minlength=K).astype(float)
        M=counts(K); q=(M@S.T)/(M@N)[:,None]
        ub[o]=np.quantile(q,LEV,axis=0).T; est[o]=S.sum(1)/N.sum()
    res={}
    for j,lab in enumerate(['no change']+['loss %g'%L for L in LOSS]):
        res[lab]=dict(realised_pp=[round(float(100*est[:,j].mean()),2),round(float(100*est[:,j].std()),2)],
                      below_zero_step200_level=rate(ub[:,j,0]<0),below_zero_later_level=rate(ub[:,j,1]<0),below_zero_95=rate(ub[:,j,2]<0))
    # constant shift on the exchange null ("read as noisy as D0's")
    for L in LOSS:
        res['shift %g on the exchange null'%L]=dict(below_zero_step200_level=rate(ub[:,0,0]-L/100<0),below_zero_later_level=rate(ub[:,0,1]-L/100<0))
    out['pool_mean']=round(float(pool),4); out['results']=res
else:
    r_back=float(sys.argv[6]); GRID=[float(v) for v in sys.argv[7].split(',')]   # net improvement in points
    p0=float(sa.mean()); assert set(np.unique(sa))<={0.0,1.0}
    Q=[(g/100+r_back*p0)/(1-p0) for g in GRID]
    lb=np.zeros((OUT,len(GRID))); est=np.zeros((OUT,len(GRID)))
    for o in range(OUT):
        pick=rng.integers(0,K,size=K); idx=np.concatenate([room_items[r] for r in pick]); cl=np.repeat(np.arange(K),sizes[pick])
        x=sa[idx]; u=rng.random(len(idx)); v=rng.random(len(idx))
        D=np.stack([np.where(x<1,(u<q).astype(float),np.where(v<r_back,0.0,1.0))-x for q in Q],0)
        S=np.stack([np.bincount(cl,weights=d,minlength=K) for d in D],0); N=np.bincount(cl,minlength=K).astype(float)
        M=counts(K); qq=(M@S.T)/(M@N)[:,None]
        lb[o]=np.quantile(qq,0.025,axis=0); est[o]=S.sum(1)/N.sum()
    pw=[float((lb[:,j]>0).mean()) for j in range(len(GRID))]
    def cross(level):
        for j in range(1,len(GRID)):
            if pw[j-1]<level<=pw[j]: return round(GRID[j-1]+(GRID[j]-GRID[j-1])*(level-pw[j-1])/(pw[j]-pw[j-1]),2)
        return None
    out.update(back_flip_rate=r_back,grid_pp=GRID,turn_right_prob=[round(q,4) for q in Q],power=[round(p,4) for p in pw],
               realised_pp=[round(float(100*est[:,j].mean()),2) for j in range(len(GRID))],
               mdi50_pp=cross(0.5),mdi80_pp=cross(0.8),mc_se_max=round(0.5/math.sqrt(OUT),4))
tag='_'.join(sys.argv[1:4])+('_r%s'%sys.argv[6] if MODE=='gate' else '')
json.dump(out,open('B5_%s.json'%tag,'w'),indent=1); print(json.dumps(out))
