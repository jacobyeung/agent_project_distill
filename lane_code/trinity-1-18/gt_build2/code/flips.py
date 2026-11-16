"""Enumerate decisions of boundary pixels (|box slack| or |z-cut| or |z-(cut-0.1)| below EPS) on an R1 build; accept only sha256 == pin."""
import numpy as np, sys, json, hashlib, io, itertools
EPS=float(sys.argv[1]); cids=sys.argv[2:]
C={p['canonical']:p['gt']['expected_sha256'] for p in json.load(open('/scratch/jjyeung/orch_cd/k1_build/work/kit_k1a/out/CAPTURES.json'))['pilot']}
def save(arrs):
    b=io.BytesIO(); np.savez_compressed(b,**arrs); return b.getvalue()
for c in cids:
    D=np.load(f'dbg/{c}_dbg.npy',allow_pickle=True).item()
    cut=D['cut']; cen,L,A,vol=D['cen'],D['L'],D['A'],D['vol']; ex=(cen[:,2]-L[:,2]/2)>=cut
    yi,xi,SHr,SWr=D['yi'],D['xi'],D['SHr'],D['SWr']
    z=np.load(f'dbg/{c}.npz'); arrs={k:z[k] for k in z.files}
    assert hashlib.sha256(save(arrs)).hexdigest()==hashlib.sha256(open(f'dbg/{c}.npz','rb').read()).hexdigest(), 'resave differs'
    order=np.argsort(vol)[::-1]
    def label(p, inbox, below):
        out=-1
        for k in order:
            m=inbox[k]
            if not ex[k] and below: m=False
            if m: out=k
        return out
    cands=[]
    for f,x in enumerate(D['pts']):
        if x is None: continue
        P,ok=x; z_=P[:,2]
        S=np.stack([(np.abs((P-cen[k])@A[k].T)-(L[k]/2+0.03)).max(1) for k in range(len(L))],1)
        bel=(z_<cut)&(z_>=cut-0.1)
        fr=ok&((np.abs(S)<EPS).any(1)|(np.abs(z_-cut)<EPS)|(np.abs(z_-(cut-0.1))<EPS))
        for i in np.nonzero(fr)[0]:
            inbox=S[i]<=0; base=label(P[i],inbox,bel[i])
            alts=set()
            for k in np.nonzero(np.abs(S[i])<EPS)[0]:
                ib=inbox.copy(); ib[k]=~ib[k]; alts.add(label(P[i],ib,bel[i]))
            if abs(z_[i]-cut)<EPS or abs(z_[i]-(cut-0.1))<EPS: alts.add(label(P[i],inbox,not bel[i]))
            alts.discard(base)
            if alts: cands.append((f,i,base,sorted(alts)))
    print(c,'candidates',len(cands),[(f,divmod(i,SWr),b,a) for f,i,b,a in cands],flush=True)
    MAXK=int(__import__('os').environ.get('MAXK','3'))
    def combos():
        for kk in range(0,MAXK+1):
            for sub in itertools.combinations(range(len(cands)),kk):
                for vals in itertools.product(*[cands[j][3] for j in sub]):
                    cb=[None]*len(cands)
                    for j,v in zip(sub,vals): cb[j]=v
                    yield cb
    n=0; found=None
    for combo in combos():
        if n>60000: break
        n+=1
        inst=arrs['inst'].copy()
        for (f,i,b,a),v in zip(cands,combo):
            if v is None: continue
            sy,sx=divmod(i,SWr); inst[f][np.ix_(yi==sy,xi==sx)]=v
        a2=dict(arrs); a2['inst']=inst
        data=save(a2)
        if hashlib.sha256(data).hexdigest()==C['arkitscenes/'+c]:
            found=combo; open(f'dbg/{c}_flip.npz','wb').write(data); break
    print(c,'tried',n,'FOUND' if found else 'none', [(cands[j][0],divmod(cands[j][1],SWr),cands[j][2],v) for j,v in enumerate(found or []) if v is not None], flush=True)
