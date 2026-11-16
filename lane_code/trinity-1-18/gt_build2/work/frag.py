import numpy as np, sys
for c in sys.argv[1:]:
    D=np.load(f'dbg/{c}_dbg.npy',allow_pickle=True).item()
    cut=D['cut']; cen,L,A,vol=D['cen'],D['L'],D['A'],D['vol']; ex=(cen[:,2]-L[:,2]/2)>=cut
    print(c,'cut %.12f'%cut)
    for f,x in enumerate(D['pts']):
        if x is None: continue
        P,ok=x
        z=P[:,2]; 
        for i in np.nonzero(ok&(np.abs(z-cut)<1e-6))[0]: print('  f',f,'px',divmod(i,D['SWr']),'z-cut %.3e'%(z[i]-cut), 'in boxes',[k for k in range(len(L)) if (np.abs((P[i]-cen[k])@A[k].T)<=L[k]/2+0.03).all()])
        for i in np.nonzero(ok&(np.abs(z-(cut-0.1))<1e-6))[0]: print('  f',f,'px',divmod(i,D['SWr']),'z-(cut-.1) %.3e'%(z[i]-cut+0.1))
        for k in range(len(L)):
            s=(np.abs((P-cen[k])@A[k].T)-(L[k]/2+0.03)).max(1)
            for i in np.nonzero(ok&(np.abs(s)<1e-6))[0]:
                others=[j for j in range(len(L)) if j!=k and (np.abs((P[i]-cen[j])@A[j].T)<=L[j]/2+0.03).all()]
                print('  f',f,'px',divmod(i,D['SWr']),'box',k,'vol %.4f'%vol[k],'slack %.3e'%s[i],'z-cut %.3f'%(z[i]-cut),'other boxes',[(j,'%.4f'%vol[j]) for j in others])
