"""Constant-shift alternatives on the exchange null of a3_power2.py (reads pass2_seed1[1-4].npz)."""
import numpy as np, glob, json
Z=[np.load(f) for f in sorted(glob.glob('pass2_seed1[1-4].npz'))]
ub=np.concatenate([z['ub'] for z in Z]); mub=np.concatenate([z['mub'] for z in Z]); est=np.concatenate([z['est'] for z in Z])
T=('route','count','easy','medium','hard','reldist','size'); out={}
for name,lev,ml in (('step200',0,0),('later',2,1)):
    r={}
    for t in range(7):
        U=ub[:,0,:,lev].copy(); U[:,t]+= -0.095; m=mub[:,0,ml]-0.095/7
        r[T[t]]=dict(type_alone=round(float((U[:,t]<0).mean()),3),stop=round(float(((U<0).any(1)|(m<0)).mean()),3))
    U=ub[:,0,:,lev]-0.02; m=mub[:,0,ml]-0.02
    r['uniform2']=dict(types=round(float((U<0).any(1).mean()),3),mean=round(float((m<0).mean()),3),stop=round(float(((U<0).any(1)|(m<0)).mean()),3))
    for c in (0.03,0.04): r['uniform%d_mean'%round(100*c)]=round(float((mub[:,0,ml]-c<0).mean()),3)
    out[name]=r
out['size_gate_95_shift']=round(float((ub[:,0,6,1]-0.095<0).mean()),3); out['null_sd_size_pp']=round(float(100*est[:,0,6].std()),2)
json.dump(out,open('A3_SHIFT_ON_EXCHANGE_NULL.json','w'),indent=1)
