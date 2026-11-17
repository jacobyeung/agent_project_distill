import json, math, glob
import numpy as np
from statistics import NormalDist
T=('route_planning','object_counting','object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard','object_rel_distance','object_size_estimation')
F=sorted(glob.glob('pass2_seed1[1-4].npz')); Z=[np.load(f) for f in F]
ub=np.concatenate([z['ub'] for z in Z]); est=np.concatenate([z['est'] for z in Z]); se=np.concatenate([z['se'] for z in Z])
mub=np.concatenate([z['mub'] for z in Z]); mest=np.concatenate([z['mest'] for z in Z]); n=len(ub)
def rate(x):
    p=float(np.mean(x)); return [round(100*p,2), round(100*math.sqrt(max(p*(1-p),1e-12)/len(x)),2)]
out=dict(files=F,outer=n,inner=int(Z[0]['INN']),rooms_union=int(Z[0]['K']),types=T,pool_mean_score=[round(float(v),4) for v in Z[0]['pool_mean']],
  model='no change: rooms resampled, arms exchanged per room with probability 1/2; loss L: later-arm item score set to 0 with probability L/(100 x mean score)',
  null_sd_pp=(100*est[:,0].std(0)).round(2).tolist(), null_mean7_sd_pp=round(float(100*mest[:,0].std()),3))
L={'bonf7':0,'p95':1,'bonf28':2}
def stop(sc,lev='bonf7',ml=0,tt=None):
    """sc: 'null', ('loss',t), 'uni'. returns boolean arrays (types any, mean, stop, per-type)"""
    U=ub[:,0,:,L[lev]].copy()
    if sc=='uni': U=ub[:,2,:,L[lev]]; m=mub[:,8,ml]
    elif sc=='null': m=mub[:,0,ml]
    else: U[:,sc[1]]=ub[:,1,sc[1],L[lev]]; m=mub[:,1+sc[1],ml]
    ty=U<0; return ty.any(1), m<0, ty.any(1)|(m<0), ty
def pack(sc,lev='bonf7',ml=0):
    a,m,s,ty=stop(sc,lev,ml); return dict(any_type=rate(a),mean=rate(m),stop=rate(s),per_type=[rate(ty[:,t])[0] for t in range(7)])
res={}
res['no change | rule: types at Bonferroni-7 level (99.643% two-sided), mean at 95%']=pack('null')
res['no change | uncorrected: types at 95%, no mean rule']=dict(any_type=rate(stop('null','p95')[0]),per_type=[rate(stop('null','p95')[3][:,t])[0] for t in range(7)])
res['no change | later-look level: types at Bonferroni-28, mean at 99.375%']=pack('null','bonf28',1)
for t in range(7):
    res['loss 9.5 on '+T[t]]=pack(('loss',t)); res['loss 9.5 on '+T[t]+' | later-look level']=pack(('loss',t),'bonf28',1)
res['uniform loss 2 on all seven']=pack('uni'); res['uniform loss 2 on all seven | later-look level']=pack('uni','bonf28',1)
res['size gate (95% interval wholly below zero) | no change']=rate(ub[:,0,6,1]<0); res['size gate | loss 9.5 on size']=rate(ub[:,1,6,1]<0)
res['realised loss, mean and sd (pp): 9.5 scenario per type']=[[round(float(100*est[:,1,t].mean()),2),round(float(100*est[:,1,t].std()),2)] for t in range(7)]
res['realised loss, uniform 2 scenario: mean of seven, mean and sd (pp)']=[round(float(100*mest[:,8].mean()),2),round(float(100*mest[:,8].std()),2)]
# normal-approximation variant of the same rule (estimate + z x bootstrap SE < 0), for comparison
zb=NormalDist().inv_cdf(1-0.025/7)
def nstop(s,tcol=None):
    E=est[:,0].copy(); Sx=se[:,0].copy()
    if s=='uni': E=est[:,2]; Sx=se[:,2]
    elif s!='null': E[:,s]=est[:,1,s]; Sx[:,s]=se[:,1,s]
    return ((E+zb*Sx)<0).any(1)
res['normal-interval variant, types only: no change / loss 9.5 on size / uniform 2']=[rate(nstop('null')),rate(nstop(6)),rate(nstop('uni'))]
out['results']=res
json.dump(out,open('A3_POWER_PASS2.json','w'),indent=1)
for k,v in res.items(): print(k,'|',json.dumps(v))
print(out['null_sd_pp'],out['null_mean7_sd_pp'],out['pool_mean_score'],n)
