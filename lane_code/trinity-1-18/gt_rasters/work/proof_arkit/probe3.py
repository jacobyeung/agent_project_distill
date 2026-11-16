import sys; sys.path.insert(0,'.')
exec(open('probe.py').read().split("f=int")[0])
f=int(sys.argv[1]); k=int(sys.argv[2])
P=world(f); Ii=I[f].reshape(-1); valid=D[f].reshape(-1)>0
loc=(P-cen[k])@A[k].T; h=L[k]/2
lab=Ii==k; oth=valid&~lab
excess=np.abs(loc)-h
for name,m in [('theirs',lab),('oth_inside',oth&(excess.max(1)<=0.032))]:
    print(name, m.sum())
    for ax in range(3):
        print('  ax',ax,'loc/h min %.3f max %.3f'%((loc[m,ax]/h[ax]).min(),(loc[m,ax]/h[ax]).max()))
print('half',h)
