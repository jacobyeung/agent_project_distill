import sys; sys.path.insert(0,'.')
exec(open('probe.py').read().split("f=int")[0])
f=int(sys.argv[1]); k=int(sys.argv[2])
P=world(f); Ii=I[f].reshape(-1); valid=D[f].reshape(-1)>0
loc=(P-cen[k])@A[k].T
need=(np.abs(loc)-L[k]/2).max(1)
lab=Ii==k
print('theirs need margin: max %.4f  p99 %.4f'%(need[lab].max(), np.percentile(need[lab],99)))
oth=valid&~lab
print('others need margin: min %.4f, count need<=0: %d, need<=0.03: %d'%(need[oth].min(), (need[oth]<=0).sum(), (need[oth]<=0.03).sum()))
yy,xx=np.divmod(np.nonzero(oth&(need<=0))[0],320)
print('unlabelled-inside pixel rows range',yy.min() if len(yy) else None, yy.max() if len(yy) else None,'cols',xx.min() if len(xx) else None,xx.max() if len(xx) else None)
# map in coarse grid
g=np.zeros((240,320),int); g.reshape(-1)[oth&(need<=0)]=1; g.reshape(-1)[lab]=2
for row in g[::12,::8]: print(''.join('.#o'[v] for v in row))
