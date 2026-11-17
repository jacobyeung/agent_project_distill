"""card_fix2, B3/B5: planning value for the VSTI gate's minimum detectable improvement on vsti_rel_dev_r0
(900 items, 150 per type, on R0-dev rooms; items.jsonl b5853845).  Step 544 has no read of this set, so the baseline
is ASSUMED: each item is right with its type's step-544 accuracy on VSTI-450 (42 / 54 / 70 for camera-object v1 / v2 / v3,
94 / 62 / 76 for object-object lr / nf / ud), independently.  The set's real rooms are used.  Later arm: wrong turns right
with probability q (one q for all six types), right turns wrong with probability r; the grid is the pooled net improvement
q x (1 - mean baseline) - r x mean baseline, so a type with a high baseline gains less and can lose under back-flips.
Gate (B3): pooled accuracy rises with its 95% room-bootstrap interval wholly above zero AND no single type's 95%
interval lies wholly below zero.  The registered value comes from the VSTI dev read of step 544 (B4).
usage: b5_vsti.py SEED OUTER INNER"""
import json, sys, math
import numpy as np
X=[json.loads(l) for l in open('/scratch/jjyeung/orch_n30/rows_r1/out/vsti_rel_dev_r0/items.jsonl')]
T=['camera_obj_rel_dist_v1','camera_obj_rel_dist_v2','camera_obj_rel_dist_v3','obj_obj_relative_pos_lr','obj_obj_relative_pos_nf','obj_obj_relative_pos_ud']
P0=np.array([0.42,0.54,0.70,0.94,0.62,0.76])
SEED,OUT,INN=int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]); rng=np.random.default_rng(SEED)
rooms=sorted({x['scene'] for x in X}); ri={s:i for i,s in enumerate(rooms)}; K=len(rooms)
rm=np.array([ri[x['scene']] for x in X]); ty=np.array([T.index(x['question_type']) for x in X])
room_items=[np.flatnonzero(rm==i) for i in range(K)]; sizes=np.array([len(v) for v in room_items])
def counts(k):
    idx=rng.integers(0,k,size=(INN,k)); idx+=np.arange(INN)[:,None]*k
    return np.bincount(idx.ravel(),minlength=INN*k).reshape(INN,k).astype(np.float64)
out=dict(items=len(X),rooms=K,items_per_room_min_median_max=[int(sizes.min()),float(np.median(sizes)),int(sizes.max())],
         per_type_items=[int((ty==t).sum()) for t in range(6)],per_type_rooms=[int(len(set(rm[ty==t]))) for t in range(6)],assumed_baseline=P0.tolist())
PB=float(P0.mean())
for r_back in (0.0,0.05):
    GRID=[0.0,1,2,3,4,5,6,8,10]; pooled=np.zeros((OUT,len(GRID)),bool); typ=np.zeros((OUT,len(GRID)),bool)
    for o in range(OUT):
        pick=rng.integers(0,K,size=K); idx=np.concatenate([room_items[r] for r in pick]); cl=np.repeat(np.arange(K),sizes[pick])
        t=ty[idx]; x=(rng.random(len(idx))<P0[t]).astype(float); u=rng.random(len(idx)); v=rng.random(len(idx))
        M=counts(K); N=np.bincount(cl,minlength=K).astype(float); den=M@N
        Nt=np.stack([np.bincount(cl,weights=(t==k).astype(float),minlength=K) for k in range(6)],1); dent=M@Nt
        for j,g in enumerate(GRID):
            q=(g/100+r_back*PB)/(1-PB); d=np.where(x<1,(u<q).astype(float),np.where(v<r_back,0.0,1.0))-x
            S=np.bincount(cl,weights=d,minlength=K); pooled[o,j]=np.quantile((M@S)/den,0.025)>0
            St=np.stack([np.bincount(cl,weights=d*(t==k),minlength=K) for k in range(6)],1)
            typ[o,j]=(np.quantile((M@St)/np.maximum(dent,1),0.975,axis=0)<0).any()
    pw=(pooled&~typ).mean(0); pp=pooled.mean(0); tf=typ.mean(0)
    def cross(level):
        for j in range(1,len(GRID)):
            if pw[j-1]<level<=pw[j]: return round(GRID[j-1]+(GRID[j]-GRID[j-1])*(level-pw[j-1])/(pw[j]-pw[j-1]),2)
        return None
    out['back_flip_rate_%g'%r_back]=dict(grid_pp=GRID,gate_passes=[round(float(p),4) for p in pw],pooled_alone=[round(float(p),4) for p in pp],
        a_type_wholly_below_zero=[round(float(p),4) for p in tf],mdi50_pp=cross(0.5),mdi80_pp=cross(0.8))
json.dump(out,open('B5_VSTI_PLANNING.json','w'),indent=1); print(json.dumps(out,indent=1))
