import sys; sys.path.insert(0,'.')
exec(open('probe.py').read().split("f=int")[0])
for f,k in [(0,2),(5,0),(10,None),(20,None)]:
    P=world(f); Ii=I[f].reshape(-1); valid=D[f].reshape(-1)>0
    ks=[k] if k is not None else [x for x in np.unique(Ii) if x>=0]
    for k in ks:
        loc=(P-cen[k])@A[k].T; h=L[k]/2; lab=Ii==k
        ex=np.abs(loc)-h
        print(f,k,'theirs: max excess x %.4f y %.4f top %.4f ; bottom gap min %.4f'%(ex[lab,0].max(),ex[lab,1].max(),(loc[lab,2]-h[2]).max(),(loc[lab,2]+h[2]).min()))
        oth=valid&~lab
        side_in=(ex[:,0]<=0.03)&(ex[:,1]<=0.03)&(loc[:,2]-h[2]<=0.03)
        print('   others with sides<=.03: bottom gap max %.4f n=%d'%(((loc[oth&side_in,2]+h[2]).max() if (oth&side_in).any() else np.nan),(oth&side_in).sum()))
