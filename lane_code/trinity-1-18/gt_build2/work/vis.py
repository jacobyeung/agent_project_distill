import numpy as np, glob, os
D='/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt'
mins=[]; tot=0; capids=[]
for f in sorted(glob.glob(D+'/*.npz')):
    z=np.load(f); inst=z['inst']; ids=z['ids']
    n=inst.shape[1]*inst.shape[2]
    cnts=[]
    for fr in inst:
        u,c=np.unique(fr[fr>=0],return_counts=True); cnts+=list(c)
    seen=np.unique(inst[inst>=0])
    mins.append(min(cnts) if cnts else None)
    capids.append((os.path.basename(f), len(ids), len(seen), min(cnts) if cnts else None, sum(np.array(cnts)<0.002*n)))
for x in capids: print(*x)
