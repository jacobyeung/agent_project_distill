import sys; sys.path.insert(0,'.')
from arkit_cr import *
r=np.load('/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/42899922.npz')
D=r['depth']; I=r['inst']; K=r['K']; C=r['c2w']
cen,L,A=r['obb_centroid'],r['obb_lengths'],r['obb_axes'].reshape(-1,3,3)
H,W=240,320
def world(f, off=0.5):
    d=D[f].astype(np.float64); v,u=np.mgrid[0:H,0:W].astype(np.float64)
    x=(u+off-K[0,2])/K[0,0]*d; y=(v+off-K[1,2])/K[1,1]*d
    P=np.stack([x,y,d,np.ones_like(d)],-1).reshape(-1,4)@C[f].astype(np.float64).T
    return P[:,:3]
f=int(sys.argv[1]) if len(sys.argv)>1 else 0
P=world(f); Ii=I[f].reshape(-1); valid=D[f].reshape(-1)>0
for k in range(len(cen)):
    loc=(P-cen[k])@A[k].T
    m=np.abs(loc)/(L[k]/2)        # normalized; inside if all<=1
    mx=m.max(1)
    lab=Ii==k
    print('box',k,'theirs n',lab.sum(),'normmax of theirs: min %.3f max %.3f'%(mx[lab].min(),mx[lab].max()) if lab.any() else '',
          'mine(<=1) n',(valid&(mx<=1)).sum())
    if lab.any():
        for ax in range(3): print('   axis',ax,'theirs |loc|/half max %.3f'%m[lab,ax].max(), ' others-valid min of max %.3f'%(mx[valid&~lab].min()))
