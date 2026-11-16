exec(open('fit.py').read().split("frames=[f")[0])
frames=[f for f in range(32) if (D[f]>0).any()]
off=float(sys.argv[1]); m=float(sys.argv[2]); mf=float(sys.argv[3])
from collections import Counter
cnt=Counter(); ex=[]
for f in frames:
    P=world(f,off); valid=D[f].reshape(-1)>0
    a=assign(P,valid,m,mf); b=I[f].reshape(-1)
    bad=np.nonzero(a!=b)[0]
    for p in bad:
        cnt[(int(a[p]),int(b[p]))]+=1
        k=b[p] if b[p]>=0 else a[p]
        loc=(P[p]-cen[k])@A[k].T
        ex.append((f,int(a[p]),int(b[p]),float((np.abs(loc)-L[k]/2).max()),float(P[p,2]-floor)))
print(cnt)
ex=np.array(ex)
for row in ex[np.argsort(ex[:,3])][::max(1,len(ex)//25)]: print(np.round(row,4))
