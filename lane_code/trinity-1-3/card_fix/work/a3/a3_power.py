"""A3: family-wise false-stop probability and power of R1's harm rule.
Inputs (read-only): step-544 arm evidence/A544.jsonl and D0 m200 ITEMS.jsonl of the read kit (job 170320).
Noise model: the paired item differences D0 m200 - step 544 on dev-S1, centred per type (true difference 0),
resampled by whole physical rooms.  Double bootstrap: the outer loop draws pseudo-reads, the inner loop
computes the tool's percentile interval on each pseudo-read.  A shift c on a type moves both the estimate and
its interval by c, so every alternative is evaluated from the stored null upper bounds."""
import json, sys, collections, math
import numpy as np
R='/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk'
A=[json.loads(l) for l in open(R+'/evidence/A544.jsonl') if l.strip()]
B=[json.loads(l) for l in open(R+'/kit/build/a4cadd8934b/fetched/x/ITEMS.jsonl') if l.strip()]
T=('route_planning','object_counting','object_rel_direction_easy','object_rel_direction_medium',
   'object_rel_direction_hard','object_rel_distance','object_size_estimation')
a={(r['family'],r['id']):r for r in A if r['family']=='main'}
b={(r['family'],r['id']):r for r in B if r['family']=='main'}
rooms=sorted({r['room'] for k,r in b.items() if r['task_type'] in T})
ri={x:i for i,x in enumerate(rooms)}; K=len(rooms)
S=np.zeros((K,7)); N=np.zeros((K,7)); acc=np.zeros((2,7)); disc=np.zeros(7)
for k,r in b.items():
    if r['task_type'] not in T: continue
    t=T.index(r['task_type']); d=r['score']-a[k]['score']
    assert a[k]['room']==r['room'] and a[k]['task_type']==r['task_type']
    S[ri[r['room']],t]+=d; N[ri[r['room']],t]+=1; acc[0,t]+=a[k]['score']; acc[1,t]+=r['score']; disc[t]+=d*d
n=N.sum(0); delta=S.sum(0)/n
out=dict(inputs=dict(a544=R+'/evidence/A544.jsonl',b200=R+'/kit/build/a4cadd8934b/fetched/x/ITEMS.jsonl'),
         types=T,items=n.tolist(),rooms_per_type=(N>0).sum(0).tolist(),rooms_union=K,
         delta_pp=(100*delta).round(3).tolist(),acc544_pp=(100*acc[0]/n).round(2).tolist(),acc200_pp=(100*acc[1]/n).round(2).tolist(),
         item_sd_of_difference_pp=(100*np.sqrt(disc/n-delta**2)).round(2).tolist())
rng=np.random.default_rng(20261117)
def counts(k,reps):
    idx=rng.integers(0,k,size=(reps,k)); idx+=np.arange(reps)[:,None]*k
    return np.bincount(idx.ravel(),minlength=reps*k).reshape(reps,k).astype(np.float64)
# 1. single-level joint bootstrap on the observed data: per-type SE, correlation, SE of the mean of seven
M=counts(K,20000); d=(M@S)/(M@N); m=d.mean(1)
se=d.std(0); out['se_pp_joint']=(100*se).round(3).tolist(); out['halfwidth95_pp_joint']=(196*se).round(2).tolist()
C=np.corrcoef(d.T); out['corr']=C.round(3).tolist(); off=C[np.triu_indices(7,1)]
out['corr_offdiag_mean_min_max']=[round(float(off.mean()),3),round(float(off.min()),3),round(float(off.max()),3)]
out['mean7_delta_pp']=round(float(100*delta.mean()),3); out['mean7_se_pp']=round(float(100*m.std()),3)
out['mean7_ci95_pp']=[round(float(100*np.quantile(m,.025)),2),round(float(100*np.quantile(m,.975)),2)]
out['mean7_se_if_independent_pp']=round(float(100*math.sqrt((se**2).sum())/7),3)
# 2. double bootstrap under no change
S0=S-N*delta   # centred: every type's true difference is 0
OUT=int(sys.argv[1]) if len(sys.argv)>1 else 4000; INN=int(sys.argv[2]) if len(sys.argv)>2 else 10000
LEV=dict(bonf7=1-0.025/7, p95=0.975, bonf10=1-0.025/10, bonf7x4=1-0.025/28)   # upper quantile of each interval
ub={k:np.zeros((OUT,7)) for k in LEV}; est=np.zeros((OUT,7)); mub=np.zeros((OUT,3)); mest=np.zeros(OUT)
for o in range(OUT):
    pick=rng.integers(0,K,size=K); s=S0[pick]; nn=N[pick]
    est[o]=s.sum(0)/nn.sum(0); mest[o]=est[o].mean()
    for t in range(7):                       # the tool's interval: resample the rooms that hold the type
        keep=nn[:,t]>0; st=s[keep,t]; nt=nn[keep,t]; Mt=counts(len(st),INN); q=(Mt@st)/(Mt@nt)
        for k,p in LEV.items(): ub[k][o,t]=np.quantile(q,p)
    Mj=counts(K,INN); q=((Mj@s)/(Mj@nn)).mean(1)   # mean of seven: resample the union of rooms
    mub[o]=np.quantile(q,[.975,.95,1-0.025/4])
np.savez('null_bounds.npz',est=est,mest=mest,mub=mub,**{'ub_'+k:v for k,v in ub.items()})
def rate(x): 
    p=float(np.mean(x)); return [round(100*p,2), round(100*math.sqrt(p*(1-p)/len(x)),2)]
def rule(shift,lev='bonf7',mcol=0):
    sh=np.asarray(shift)/100.0
    ty=(ub[lev]+sh<0); me=(mub[:,mcol]+sh.mean()<0)
    return dict(any_type=rate(ty.any(1)),mean=rate(me),stop=rate(ty.any(1)|me),per_type=[rate(ty[:,t])[0] for t in range(7)])
res={}
res['null_rule_A3 (types Bonferroni-7, mean 95%)']=rule(np.zeros(7))
res['null_uncorrected (types 95%, no mean rule)']=dict(any_type=rate((ub['p95']<0).any(1)),per_type=[rate(ub['p95'][:,t]<0)[0] for t in range(7)])
res['null_types Bonferroni-10 (seven direct + three camera share 2.5%)']=rule(np.zeros(7),'bonf10')
res['null_types Bonferroni-28 (four looks), mean 99.375%']=rule(np.zeros(7),'bonf7x4',2)
for t in range(7):
    sh=np.zeros(7); sh[t]=-9.5; res['loss 9.5 on '+T[t]]=rule(sh)
    res['loss 9.5 on '+T[t]+' (Bonferroni-28 look level)']=rule(sh,'bonf7x4',2)
for c in (-1,-2,-3,-4,-5): res['uniform loss %d on all seven'%(-c)]=rule(np.full(7,float(c)))
res['uniform loss 2 (Bonferroni-28 look level)']=rule(np.full(7,-2.0),'bonf7x4',2)
out['double_bootstrap']=dict(outer=OUT,inner=INN,results=res,
    coverage_note='rates are percent with their Monte Carlo standard error',
    null_estimate_sd_pp=(100*est.std(0)).round(3).tolist(),null_mean7_sd_pp=round(float(100*mest.std()),3))
# 3. Gaussian check with the joint covariance
G=rng.multivariate_normal(np.zeros(7),np.cov(d.T),size=1000000); zb=-float(np.quantile(rng.standard_normal(4000000),0.025/7))
from statistics import NormalDist
zb=NormalDist().inv_cdf(1-0.025/7); sm=m.std()
def grule(shift):
    sh=np.asarray(shift)/100.0; x=G+sh; ty=(x+zb*se<0); me=(x.mean(1)+1.96*sm<0)
    return dict(any_type=round(100*float(ty.any(1).mean()),2),mean=round(100*float(me.mean()),2),stop=round(100*float((ty.any(1)|me).mean()),2))
gs={'null':grule(np.zeros(7)),'uniform loss 2':grule(np.full(7,-2.0))}
for t in range(7):
    sh=np.zeros(7); sh[t]=-9.5; gs['loss 9.5 on '+T[t]]=grule(sh)
out['gaussian_check']=dict(z_bonf7=round(zb,3),results=gs)
json.dump(out,open('A3_POWER.json','w'),indent=1)
print(json.dumps(out,indent=1))
