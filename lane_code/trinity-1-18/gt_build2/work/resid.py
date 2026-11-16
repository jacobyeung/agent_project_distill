import numpy as np, sys
from relift import relift
from why3 import lift
for fn in sys.argv[1:]:
    z=np.load(fn); I=relift(z,floor='exemptA'); O=z['inst']; per,(SHr,SWr)=lift(z)
    cen=z['obb_centroid']; L=z['obb_lengths']; A=z['obb_axes'].reshape(-1,3,3)
    p2=np.percentile(np.concatenate([Q[ok,2] for x in per if x for Q,ok,_ in [x]]),2); cut=p2+0.05
    ex=(cen[:,2]-L[:,2]/2)>=cut
    _,H,W=O.shape; yi=np.floor(np.arange(H)*SHr/H).astype(int); xi=np.floor(np.arange(W)*SWr/W).astype(int)
    print(fn[-12:],'cut',cut,'exempt',np.nonzero(ex)[0], 'labels',list(z['labels']))
    for f,y,x in zip(*np.nonzero(I!=O)):
        Q,ok,src=per[f]; i=yi[y]*SWr+xi[x]; p=Q[i]
        slack=[(k, (np.abs((p-cen[k])@A[k].T)-(L[k]/2+0.03)).max()) for k in range(len(L))]
        ins=[(k,'%.2e'%s) for k,s in slack if s<=0.01]
        print(' f',f,'y',y,'x',x,'src',yi[y],xi[x],'orig',O[f,y,x],'ours',I[f,y,x],'z-cut %.5f'%(p[2]-cut),'ok',ok[i],'boxes(slack<=1cm)',ins)
