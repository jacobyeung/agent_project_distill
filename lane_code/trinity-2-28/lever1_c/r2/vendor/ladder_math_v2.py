"""Registered v2 fusion and object merging; all constants fixed by the spec."""
from collections import Counter
import numpy as np

RULES=('best1','trim','allspread')+tuple(f'vote_{v}_{m}{s}' for s in ('_best','') for v in (5,10) for m in (2,3))
TAUS=(.25,.15,.40)

def fusion_box(points,best,rule,min_area_box):
    parts={int(f):np.asarray(p,float).reshape(-1,3) for f,p in points.items()}
    if len(parts)==1 or rule=='best1':return min_area_box(parts[best])
    if rule in ('trim','allspread'):
        p=np.concatenate([parts[f] for f in sorted(parts)])
    else:
        _,v,m,*suffix=rule.split('_');v=float(v)/100;m=int(m)
        if len(parts)<m:return min_area_box(parts[best])
        vox={f:list(map(tuple,np.floor(p/v).astype(np.int64))) for f,p in parts.items()}
        counts=Counter(x for vals in vox.values() for x in set(vals))
        supported=[parts[f][np.array([counts[x]>=m for x in vox[f]],bool)] for f in sorted(parts)]
        if suffix:supported.append(parts[best])
        p=np.concatenate(supported)
    box=min_area_box(p)
    if rule=='trim':
        axes=box['normalizedAxes'];lo,hi=np.percentile(p@axes.T,[2,98],axis=0)
        if np.any(hi<=lo):raise ValueError('degenerate_trim_box')
        box=dict(centroid=((lo+hi)/2)@axes,axesLengths=hi-lo,normalizedAxes=axes)
    return box

def merge(tracks,tau):
    from student_pilot.routed_candidates import overlap
    objs=[dict(index=i,ids={i},members={p.frame:p for p in c.proposals},voxels=c.voxels) for i,c in enumerate(tracks)]
    while True:
        candidates=[]
        for i,a in enumerate(objs):
            for j in range(i):
                b=objs[j];ov=overlap(a['voxels'],b['voxels'])
                if ov<tau:continue
                common=a['members'].keys() & b['members'].keys()
                if any(np.count_nonzero(a['members'][f].mask & b['members'][f].mask)/max(1,min(a['members'][f].mask.sum(),b['members'][f].mask.sum()))<.5 for f in common):continue
                candidates.append((-ov,min(a['index'],b['index']),max(a['index'],b['index']),j,i))
        if not candidates:return objs
        _,_,_,j,i=min(candidates);a,b=objs[j],objs[i];members=dict(a['members'])
        for f,p in b['members'].items():
            if f not in members or (p.mask.sum(),p.joint,-p.index)>(members[f].mask.sum(),members[f].joint,-members[f].index):members[f]=p
        obj=dict(index=min(a['index'],b['index']),ids=a['ids']|b['ids'],members=members,
            voxels=frozenset().union(*(p.voxels for p in members.values())))
        objs=[o for k,o in enumerate(objs) if k not in (i,j)]+[obj];objs.sort(key=lambda o:o['index'])

def mra(pred,gt):
    if pred is None:return 0.
    return float(np.mean([abs(pred-gt)/abs(gt)<1-t for t in np.arange(.5,.96,.05)]))

def folds(rooms):
    rooms=sorted(set(rooms));order=np.random.default_rng(20261119).permutation(len(rooms))
    return {rooms[int(i)]:k%5 for k,i in enumerate(order)}
