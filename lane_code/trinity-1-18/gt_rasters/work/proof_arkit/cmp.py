import ctypes; ctypes.CDLL(None).prctl(41,1,0,0,0)
import numpy as np, sys
a=np.load(sys.argv[1]); b=np.load(sys.argv[2])
for k in b.files:
    x,y=a[k],b[k]; eq=x.shape==y.shape and x.dtype==y.dtype and np.array_equal(x,y)
    if not eq: print(k, x.dtype, y.dtype, x.shape, y.shape, (np.abs(x.astype(float)-y.astype(float)).max() if x.shape==y.shape and x.dtype.kind in 'fiu' else ''))
d=a['depth']; e=b['depth']
print('zero frames mine', [f for f in range(32) if not (d[f]>0).any()], 'theirs', [f for f in range(32) if not (e[f]>0).any()])
print('per-frame depth eq', [int(np.array_equal(d[f],e[f])) for f in range(32)])
print('inst mismatch per frame', [(f,int((a['inst'][f]!=b['inst'][f]).sum())) for f in range(32) if (a['inst'][f]!=b['inst'][f]).any()])
if 'labels' in b.files and not np.array_equal(a['labels'],b['labels']): print(a['labels'].tolist(), b['labels'].tolist())
