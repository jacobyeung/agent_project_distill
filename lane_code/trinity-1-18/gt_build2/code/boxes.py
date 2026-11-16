import numpy as np, sys, os
from why3 import lift
for fn in sys.argv[1:]:
    z=np.load(fn); per,_=lift(z)
    cen=z['obb_centroid']; L=z['obb_lengths']; A=z['obb_axes'].reshape(-1,3,3)
    p2=np.percentile(np.concatenate([Q[ok,2] for x in per if x for Q,ok,_ in [x]]),2); cut=p2+0.05
    for k in range(len(L)):
        nb=0; kept=0
        for x in per:
            if x is None: continue
            Q,ok,src=x; ink=(np.abs((Q-cen[k])@A[k].T)<=L[k]/2+0.03).all(1)&ok
            b=ink&(Q[:,2]<cut); nb+=b.sum(); kept+=(src[b]==k).sum()
        if nb:
            low=cen[k][2]-np.abs(A[k][:,2])@(L[k]/2)
            print(os.path.basename(fn)[:8], k, z['labels'][k], 'below',nb,'kept',kept, 'low-cut %.4f'%(low-cut), 'low-p2 %.4f'%(low-p2), 'aa_bottom-cut %.4f'%(cen[k][2]-L[k][2]/2-cut), flush=True)
