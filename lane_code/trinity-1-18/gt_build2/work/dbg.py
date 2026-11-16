import numpy as np, sys
for c in sys.argv[1:]:
    D=np.load(f'dbg/{c}_dbg.npy',allow_pickle=True).item()
    cut=D['cut']; cen,L,A,vol=D['cen'],D['L'],D['A'],D['vol']
    bot=cen[:,2]-L[:,2]/2
    print(c,'rot',D['rot'],'cut',cut,'nbox',len(L))
    print('  bottom-cut sorted |.|<0.01:',[(k,'%.5f'%(bot[k]-cut)) for k in np.argsort(np.abs(bot-cut)) if abs(bot[k]-cut)<0.01])
    vs=np.sort(vol); print('  min rel vol gap %.2e'%(np.min(np.diff(vs)/vs[1:])))
    nz=[0,0,0,0]
    for x in D['pts']:
        if x is None: continue
        P,ok=x; z=P[ok,2]
        nz[0]+=(np.abs(z-cut)<1e-7).sum(); nz[1]+=(np.abs(z-(cut-0.1))<1e-7).sum()
        Q=P[ok]
        for k in range(len(L)):
            s=(np.abs((Q-cen[k])@A[k].T)-(L[k]/2+0.03)).max(1)
            nz[2]+=(np.abs(s)<1e-7).sum(); nz[3]+=(np.abs(s)<1e-5).sum()
    print('  px |z-cut|<1e-7:',nz[0],' |z-(cut-0.1)|<1e-7:',nz[1],' box slack<1e-7:',nz[2],' <1e-5:',nz[3])
